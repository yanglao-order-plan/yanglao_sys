import torch
import json
from detectron2.utils.events import get_event_storage
from detectron2.modeling.meta_arch.build import META_ARCH_REGISTRY
from detectron2.modeling.meta_arch import GeneralizedRCNN


@META_ARCH_REGISTRY.register()
class UnifiedRCNN(GeneralizedRCNN):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.unified_eval = cfg.MULTI_DATASET.UNIFIED_EVAL
        self.datasets = cfg.MULTI_DATASET.DATASETS
        self.num_datasets = len(self.datasets)
        self.dataset_name_to_id = {k: i for i, k in enumerate(self.datasets)}
        self.eval_dataset = -1
        self.cpu_post_process = cfg.CPU_POST_PROCESS # due to memory issue on mask

        label_map = json.load(
            open(cfg.MULTI_DATASET.UNIFIED_LABEL_FILE, 'r'))['label_map']
        self.label_map = {
            self.datasets.index(d): torch.tensor(x).long().to(
            torch.device(cfg.MODEL.DEVICE)) \
            for d, x in label_map.items() if d in self.datasets}

    def forward(self, batched_inputs):
        if not self.training:
            return self.inference(batched_inputs)
        images = self.preprocess_image(batched_inputs)
        gt_instances = [x["instances"].to(self.device) for x in batched_inputs]

        for i in range(len(gt_instances)):
            dataset_source = batched_inputs[i]['dataset_source']
            gt_instances[i]._dataset_source = dataset_source
            gt_instances[i].gt_classes = \
                self.label_map[dataset_source][gt_instances[i].gt_classes]
        
        features = self.backbone(images.tensor) # #lvl
        proposals, proposal_losses = self.proposal_generator(
            images, features, gt_instances)
        
        _, detector_losses = self.roi_heads(
            images, features, proposals, gt_instances)
        if self.vis_period > 0:
            storage = get_event_storage()
            if storage.iter % self.vis_period == 0:
                self.visualize_training(batched_inputs, proposals)
        
        losses = {}
        losses.update(proposal_losses)
        losses.update(detector_losses)
        return losses

    def inference(self, batched_inputs, detected_instances=None, 
        do_postprocess=True):
        # support eval_dataset and cpu post process
        assert not self.training
        assert detected_instances is None
        images = self.preprocess_image(batched_inputs)
        features = self.backbone(images.tensor)
        proposals, _ = self.proposal_generator(images, features, None)
        results, _ = self.roi_heads(
            images, features, proposals, None, eval_dataset=self.eval_dataset)
        
        if do_postprocess:
            if self.cpu_post_process:
                for r in results:
                    r = r.to('cpu')
            return GeneralizedRCNN._postprocess(
                results, batched_inputs, images.image_sizes)
        else:
            return results

    def set_eval_dataset(self, dataset_name):
        meta_datase_name = dataset_name[:dataset_name.find('_')]
        if self.unified_eval:
            self.eval_dataset = -1
        else:
            self.eval_dataset = \
                self.dataset_name_to_id[meta_datase_name]

