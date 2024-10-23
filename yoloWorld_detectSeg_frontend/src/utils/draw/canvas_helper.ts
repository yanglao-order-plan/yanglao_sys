const canvasScaleInitializer = ({
    width,
    height,
    containerRef,
    shouldFitToWidth,
}: {
    width: number;
    height: number;
    containerRef: HTMLElement;
    shouldFitToWidth: boolean;
}): CanvasScaleResult => {
const containerWidth = containerRef.offsetWidth || width;
const containerHeight = containerRef.offsetHeight || height;
return canvasScaleResizer({
width,
height,
containerWidth,
containerHeight,
shouldFitToWidth,
});
};

const canvasScaleResizer = ({
width,
height,
containerWidth,
containerHeight,
shouldFitToWidth,
}: {
width: number;
height: number;
containerWidth: number;
containerHeight: number;
shouldFitToWidth: boolean;
}): CanvasScaleResult => {
let scale = 1;
const xScale = containerWidth / width;
const yScale = containerHeight / height;
if (shouldFitToWidth) {
scale = xScale;
} else {
scale = Math.min(xScale, yScale);
}
const scaledWidth = scale * width;
const scaledHeight = scale * height;
const scalingStyle = {
transform: `scale(${scale})`,
transformOrigin: "left top",
};
const scaledDimensionsStyle = {
width: scaledWidth,
height: scaledHeight,
};
return {
scalingStyle,
scaledDimensionsStyle,
scaledWidth,
scaledHeight,
containerWidth,
containerHeight,
};
};

interface CanvasScaleResult {
scalingStyle: {
transform: string;
transformOrigin: string;
};
scaledDimensionsStyle: {
width: number;
height: number;
};
scaledWidth: number;
scaledHeight: number;
containerWidth: number;
containerHeight: number;
}

export { canvasScaleInitializer, canvasScaleResizer };
