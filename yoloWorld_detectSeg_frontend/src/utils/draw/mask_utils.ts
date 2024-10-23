/**
 * Parses RLE from compressed string
 * @param {Array<number>} input
 * @returns array of integers
 */
export const rleFrString = (input: string): number[] => {
    let result: number[] = [];
    let charIndex = 0;
    while (charIndex < input.length) {
        let value = 0,
            k = 0,
            more = 1;
        while (more) {
            let c = input.charCodeAt(charIndex) - 48; // Get char code and adjust
            value |= (c & 0x1f) << (5 * k); // Update value
            more = c & 0x20; // Check if more bits are needed
            charIndex++;
            k++;
            if (!more && (c & 0x10)) value |= -1 << (5 * k); // Handle negative numbers
        }
        // Apply delta encoding
        if (result.length > 2) value += result[result.length - 2];

        result.push(value);
    }
    return result;
};


/**
 * Parse RLE to mask array
 * @param rows
 * @param cols
 * @param counts
 * @returns {Uint8Array}
 */
export const decodeRleCounts = ([rows, cols]: [number, number], counts: number[]): Uint8Array => {
    let arr = new Uint8Array(rows * cols);
    let i = 0;
    let flag = 0;
    for (let k of counts) {
        while (k-- > 0) {
            arr[i++] = flag;
        }
        flag = (flag + 1) % 2;
    }
    return arr;
};


/**
 * Parse Everything mode counts array to mask array
 * @param rows
 * @param cols
 * @param counts
 * @returns {Uint8Array}
 */
export const decodeEverythingMask = ([rows, cols]: [number, number], counts: number[]): Uint8Array => {
    let arr = new Uint8Array(rows * cols);
    let k = 0;
    for (let i = 0; i < counts.length; i += 2) {
        for (let j = 0; j < counts[i]; j++) {
            arr[k++] = counts[i + 1];
        }
    }
    return arr;
};


/**
 * Get globally unique color in the mask
 * @param category
 * @param colorMap
 * @returns {*}
 */
interface Color {
    r: number;
    g: number;
    b: number;
}

interface ColorMap {
    [category: string]: Color;
}

export const getUniqueColor = (category: string, colorMap: ColorMap): Color => {
    // 该种类没有颜色
    if (!colorMap.hasOwnProperty(category)) {
        // 生成唯一的颜色
        while (true) {
            const color: Color = {
                r: Math.floor(Math.random() * 256),
                g: Math.floor(Math.random() * 256),
                b: Math.floor(Math.random() * 256)
            };
            // 检查颜色映射中是否已存在相同的颜色
            const existingColors = Object.values(colorMap);
            const isDuplicateColor = existingColors.some((existingColor) => {
                return color.r === existingColor.r && color.g === existingColor.g && color.b === existingColor.b;
            });
            // 如果不存在相同颜色，结束循环
            if (!isDuplicateColor) {
                colorMap[category] = color;
                break;
            }
        }
        console.log("生成唯一颜色", category, colorMap[category]);
        return colorMap[category];
    } else {
        return colorMap[category];
    }
};

/**
 * Cut out specific area of image uncovered by mask
 * @param w image's natural width
 * @param h image's natural height
 * @param image source image
 * @param canvas mask canvas
 * @param callback function to solve the image blob
 */
interface Size {
    w: number;
    h: number;
}
interface Color {
    r: number;
    g: number;
    b: number;
}


/**
 * Cut out specific area of image covered by target color mask
 * PS: 我写的这代码有问题，比较color的时候tmd明明mask canvas中有这个颜色，
 * 就是说不存在这颜色，所以不用这个函数，改成下面的了
 * @param w image's natural width
 * @param h image's natural height
 * @param image source image
 * @param canvas mask canvas
 * @param color target color
 * @param callback function to solve the image blob
 */
export const cutOutImageWithMaskColor = (
    { w, h }: Size,
    image: HTMLImageElement,
    canvas: HTMLCanvasElement,
    color: Color,
    callback?: (blob: Blob | null) => void
): void => {
    const resultCanvas = document.createElement('canvas');
    const resultCtx = resultCanvas.getContext('2d', { willReadFrequently: true })!;
    const originalCtx = canvas.getContext('2d', { willReadFrequently: true })!;

    resultCanvas.width = w;
    resultCanvas.height = h;
    resultCtx.drawImage(image, 0, 0, w, h);

    const maskDataArray = originalCtx.getImageData(0, 0, w, h).data;
    const imageData = resultCtx.getImageData(0, 0, w, h);
    const imageDataArray = imageData.data;

    let find = false;

    // 比较 mask 的 color 和目标 color
    for (let i = 0; i < maskDataArray.length; i += 4) {
        const r = maskDataArray[i],
            g = maskDataArray[i + 1],
            b = maskDataArray[i + 2];
        if (r !== color.r || g !== color.g || b !== color.b) { // 颜色与目标颜色不相同，是 mask 区域
            imageDataArray[i + 3] = 0; // 设置 alpha 为 0
        } else {
            find = true;
        }
    }

    // 计算被分割出来的部分的矩形框
    let minX = w;
    let minY = h;
    let maxX = 0;
    let maxY = 0;

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const alpha = imageDataArray[(y * w + x) * 4 + 3];
            if (alpha !== 0) {
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
            }
        }
    }

    const width = maxX - minX + 1;
    const height = maxY - minY + 1;
    const startX = minX;
    const startY = minY;

    resultCtx.putImageData(imageData, 0, 0);

    // 创建一个新的 canvas 来存储特定区域的图像
    const croppedCanvas = document.createElement('canvas');
    const croppedContext = croppedCanvas.getContext('2d')!;
    croppedCanvas.width = width;
    croppedCanvas.height = height;

    // 将特定区域绘制到新 canvas 上
    croppedContext.drawImage(resultCanvas, startX, startY, width, height, 0, 0, width, height);

    // 导出裁剪后的图像
    croppedCanvas.toBlob((blob) => {
        if (callback) {
            callback(blob);
        }
    }, 'image/png');
};

type CategoryArray = number[];  // 假设类别数组是由数字组成的
type CallbackFunction = (blob: Blob | null) => void;
/**
 * Cut out specific area whose category is target category
 * @param w image's natural width
 * @param h image's natural height
 * @param image source image
 * @param arr original mask array that stores all pixel's category
 * @param category target category
 * @param callback function to solve the image blob
 */
export const cutOutImageWithCategory = (
    { w, h }: Size,
    image: HTMLImageElement,
    arr: CategoryArray,   // 类别数组
    category: number,     // 目标类别
    callback?: CallbackFunction // 可选的回调函数
): void => {
    const resultCanvas = document.createElement('canvas');
    const resultCtx = resultCanvas.getContext('2d', { willReadFrequently: true })!;
    
    resultCanvas.width = w;
    resultCanvas.height = h;
    resultCtx.drawImage(image, 0, 0, w, h);

    const imageData = resultCtx.getImageData(0, 0, w, h);
    const imageDataArray = imageData.data;

    // 比较 mask 的类别和目标类别
    let i = 0;
    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            if (category !== arr[i++]) { // 类别不相同，是 mask 区域
                imageDataArray[3 + (w * y + x) * 4] = 0; // 设置 alpha 为 0
            }
        }
    }

    // 计算被分割出来的部分的矩形框
    let minX = w;
    let minY = h;
    let maxX = 0;
    let maxY = 0;

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const alpha = imageDataArray[(y * w + x) * 4 + 3];
            if (alpha !== 0) {
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
            }
        }
    }

    const width = maxX - minX + 1;
    const height = maxY - minY + 1;
    const startX = minX;
    const startY = minY;

    resultCtx.putImageData(imageData, 0, 0);

    // 创建一个新的 canvas 来存储特定区域的图像
    const croppedCanvas = document.createElement("canvas");
    const croppedContext = croppedCanvas.getContext("2d")!;
    croppedCanvas.width = width;
    croppedCanvas.height = height;

    // 将特定区域绘制到新 canvas 上
    croppedContext.drawImage(resultCanvas, startX, startY, width, height, 0, 0, width, height);

    // 导出裁剪后的图像
    croppedCanvas.toBlob(blob => {
        if (callback) {
            callback(blob);
        }
    }, "image/png");
};