import cv2
import numpy
import numpy as np

from . import Shape, AutoLabelingResult, YOLO,numpy_nms, xywh2xyxy, rescale_box_and_landmark
from ..utils import xyxyxyxy_to_xyxy

# 最终的人脸对齐图像尺寸分为两种：112x96和112x112，并分别对应结果图像中的两组仿射变换目标点,如下所示
imgSize1 = [112, 96]
imgSize2 = [112, 112]
coord5point1 = [[30.2946, 51.6963],  # 112x96的目标点
                [65.5318, 51.6963],
                [48.0252, 71.7366],
                [33.5493, 92.3655],
                [62.7299, 92.3655]]
coord5point2 = [[30.2946 + 8.0000, 51.6963],  # 112x112的目标点
                [65.5318 + 8.0000, 51.6963],
                [48.0252 + 8.0000, 71.7366],
                [33.5493 + 8.0000, 92.3655],
                [62.7299 + 8.0000, 92.3655]]

def transformation_from_points(points1, points2):
    points1 = points1.astype(numpy.float64)
    points2 = points2.astype(numpy.float64)
    c1 = numpy.mean(points1, axis=0)
    c2 = numpy.mean(points2, axis=0)
    points1 -= c1
    points2 -= c2
    s1 = numpy.std(points1)
    s2 = numpy.std(points2)
    points1 /= s1
    points2 /= s2
    U, S, Vt = numpy.linalg.svd(points1.T * points2)
    R = (U * Vt).T
    return numpy.vstack([numpy.hstack(((s2 / s1) * R, c2.T - (s2 / s1) * R * c1.T)), numpy.matrix([0., 0., 1.])])


def warp_im(img_im, orgi_landmarks, tar_landmarks):
    pts1 = numpy.float64(numpy.matrix([[point[0], point[1]] for point in orgi_landmarks]))
    pts2 = numpy.float64(numpy.matrix([[point[0], point[1]] for point in tar_landmarks]))
    M = transformation_from_points(pts1, pts2)
    dst = cv2.warpAffine(img_im, M[:2], (img_im.shape[1], img_im.shape[0]))
    return dst

class YOLOv6Face(YOLO):
    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = [
            "button_run",
            "input_conf",
            "edit_conf",
        ]
        output_modes = {
            "rectangle": "Rectangle",
            "polygon": "Polygon",
        }
        default_output_mode = "rectangle"

    def __init__(self, model_config, on_message) -> None:
        super().__init__(model_config, on_message)
        self.scale = self.config.get("scale", "112x112")

    def postprocess(
        self,
        prediction,
        multi_label=False,
        max_det=1000,
    ):
        """
        Post-process the network's output, to get the
        bounding boxes, key-points and their confidence scores.
        """

        """Runs Non-Maximum Suppression (NMS) on inference results.
        Args:
            prediction: (tensor), with shape [N, 15 + num_classes], N is the number of bboxes.
            multi_label: (bool), when it is set to True, one box can have multi labels,
                otherwise, one box only huave one label.
            max_det:(int), max number of output bboxes.
        Returns:
            list of detections, echo item is one tensor with shape (num_boxes, 16),
                16 is for [xyxy, ldmks, conf, cls].
        """
        num_classes = prediction.shape[2] - 15  # number of classes
        pred_candidates = np.logical_and(
            prediction[..., 14] > self.conf_thres,
            np.max(prediction[..., 15:], axis=-1) > self.conf_thres,
        )

        # Function settings.
        max_wh = 4096  # maximum box width and height
        max_nms = (
            30000  # maximum number of boxes put into torchvision.ops.nms()
        )
        multi_label &= num_classes > 1  # multiple labels per box

        output = [np.zeros((0, 16))] * prediction.shape[0]

        for img_idx, x in enumerate(
            prediction
        ):  # image index, image inference
            x = x[pred_candidates[img_idx]]  # confidence

            # If no box remains, skip the next process.
            if not x.shape[0]:
                continue

            # confidence multiply the objectness
            x[:, 15:] *= x[:, 14:15]  # conf = obj_conf * cls_conf

            # (center x, center y, width, height) to (x1, y1, x2, y2)
            box = xywh2xyxy(x[:, :4])

            # Detections matrix's shape is  (n,16), each row represents (xyxy, conf, cls, lmdks)
            if multi_label:
                box_idx, class_idx = np.nonzero(x[:, 15:] > self.conf_thres).T
                x = np.concatenate(
                    (
                        box[box_idx],
                        x[box_idx, class_idx + 15, None],
                        class_idx[:, None].astype(np.float32),
                        x[box_idx, 4:14],
                    ),
                    1,
                )
            else:
                conf = np.max(x[:, 15:], axis=1, keepdims=True)
                class_idx = np.argmax(x[:, 15:], axis=1, keepdims=True)
                x = np.concatenate(
                    (box, conf, class_idx.astype(np.float32), x[:, 4:14]), 1
                )[conf.ravel() > self.conf_thres]

            # Filter by class, only keep boxes whose category is in classes.
            if self.filter_classes:
                fc = [
                    i
                    for i, item in enumerate(self.classes)
                    if item in self.filter_classes
                ]
                x = x[(x[:, 5:6] == np.array(fc)).any(1)]

            # Check shape
            num_box = x.shape[0]  # number of boxes
            if not num_box:  # no boxes kept.
                continue
            elif num_box > max_nms:  # excess max boxes' number.
                x = x[
                    x[:, 4].argsort(descending=True)[:max_nms]
                ]  # sort by confidence

            # Batched NMS
            class_offset = x[:, 5:6] * (
                0 if self.agnostic else max_wh
            )  # classes
            boxes, scores = (
                x[:, :4] + class_offset,
                x[:, 4],
            )  # boxes (offset by class), scores

            keep_box_idx = numpy_nms(boxes, scores, self.iou_thres)  # NMS
            if keep_box_idx.shape[0] > max_det:  # limit detections
                keep_box_idx = keep_box_idx[:max_det]

            output[img_idx] = x[keep_box_idx]

        return output

    def key_transform(self, img_im, bounding_box, points):
        shape = img_im.shape
        height = shape[0]
        width = shape[1]
        x1, y1, x2, y2 = bounding_box
        # 外扩大100%，防止对齐后人脸出现黑边
        new_x1 = max(int(1.50 * x1 - 0.50 * x2), 0)
        new_x2 = min(int(1.50 * x2 - 0.50 * x1), width - 1)
        new_y1 = max(int(1.50 * y1 - 0.50 * y2), 0)
        new_y2 = min(int(1.50 * y2 - 0.50 * y1), height - 1)

        # 得到原始图中关键点坐标
        left_eye_x, left_eye_y = points[:2]
        right_eye_x, right_eye_y = points[2:4]
        nose_x, nose_y = points[4:6]
        left_mouth_x, left_mouth_y = points[6:8]
        right_mouth_x, right_mouth_y = points[8:10]

        # 得到外扩100%后图中关键点坐标
        new_left_eye_x = left_eye_x - new_x1
        new_right_eye_x = right_eye_x - new_x1
        new_nose_x = nose_x - new_x1
        new_left_mouth_x = left_mouth_x - new_x1
        new_right_mouth_x = right_mouth_x - new_x1
        new_left_eye_y = left_eye_y - new_y1
        new_right_eye_y = right_eye_y - new_y1
        new_nose_y = nose_y - new_y1
        new_left_mouth_y = left_mouth_y - new_y1
        new_right_mouth_y = right_mouth_y - new_y1

        face_landmarks = [[new_left_eye_x, new_left_eye_y],  # 在扩大100%人脸图中关键点坐标
                          [new_right_eye_x, new_right_eye_y],
                          [new_nose_x, new_nose_y],
                          [new_left_mouth_x, new_left_mouth_y],
                          [new_right_mouth_x, new_right_mouth_y]]
        face = img_im[new_y1: new_y2, new_x1: new_x2]  # 扩大100%的人脸区域
        if self.scale == '112x96':
            dst = warp_im(face, face_landmarks, coord5point1)  # 112x96对齐后尺寸
            crop_im = dst[0:imgSize1[0], 0:imgSize1[1]]
        elif self.scale == '112x112':
            dst = warp_im(face, face_landmarks, coord5point2)  # 112x112对齐后尺寸
            crop_im = dst[0:imgSize2[0], 0:imgSize2[1]]
        else:
            raise ValueError("scale must be 112x96 or 112x112")
        return crop_im

    def predict_shapes(self, image, image_path=None):
        """
        Predict shapes from image
        """

        if image is None:
            return []
        input_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        blob = self.preprocess(input_image)
        predictions = self.net.get_ort_inference(blob)
        results = self.postprocess(predictions)[0]

        if len(results) == 0:
            return AutoLabelingResult([], replace=True)
        results[:, :4], results[:, -10:] = rescale_box_and_landmark(
            self.input_shape, results[:, :4], results[:, -10:], image.shape
        )

        shapes, avatars = [], []
        for i, r in enumerate(reversed(results)):
            xyxy, score, cls_id, lmdks = r[:4], r[4], r[5], r[6:]
            if score < self.conf_thres:
                continue
            x1, y1, x2, y2 = list(map(int, xyxy))
            lmdks = list(map(int, lmdks))
            label = str(self.classes[int(cls_id)])
            rectangle_shape = Shape(
                label=label,
                shape_type="rectangle",
                group_id=int(i),
                score=float(score),
            )
            rectangle_shape.add_point(x1, y1)
            rectangle_shape.add_point(x2, y1)
            rectangle_shape.add_point(x2, y2)
            rectangle_shape.add_point(x1, y2)
            shapes.append(rectangle_shape)
            kpt_names = self.keypoint_name[label]
            kpoints = []
            for j in range(0, len(lmdks), 2):
                x, y = lmdks[j], lmdks[j + 1]
                point_shape = Shape(
                    label=kpt_names[j // 2],
                    shape_type="point",
                    group_id=int(i),
                ) # 关键点（三个）
                point_shape.add_point(x, y)
                kpoints.append((x, y))
                shapes.append(point_shape)
            if self.scale is not None:
                crop_img = self.key_transform(image.copy(), xyxy, lmdks)
                avatars.append(crop_img)
        result = AutoLabelingResult(shapes, avatars=avatars, replace=True)

        return result

    def unload(self):
        del self.net
