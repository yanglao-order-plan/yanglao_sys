// Decode from RLE to Binary Mask
// (pass false to flat argument if you need 2d matrix output)
export function decodeCocoRLE(
    [rows, cols]: [number, number],
    counts: number[],
    flat: boolean = true
): number[] | number[][] {
    let pixelPosition = 0;
    let binaryMask: number[] | number[][];

    if (flat) {
        binaryMask = Array(rows * cols).fill(0);
    } else {
        binaryMask = Array.from({ length: rows }, (_) => Array(cols).fill(0));
    }

    for (let i = 0, rleLength = counts.length; i < rleLength; i += 2) {
        let zeros = counts[i],
            ones = counts[i + 1] ?? 0;

        pixelPosition += zeros;

        while (ones > 0) {
            const rowIndex = pixelPosition % rows,
                colIndex = (pixelPosition - rowIndex) / rows;

            if (flat) {
                const arrayIndex = rowIndex * cols + colIndex;
                (binaryMask as number[])[arrayIndex] = 1;
            } else {
                (binaryMask as number[][])[rowIndex][colIndex] = 1;
            }

            pixelPosition++;
            ones--;
        }
    }

    if (!flat) {
        console.log("Result matrix:");
        (binaryMask as number[][]).forEach((row, i) => console.log(row.join(" "), `- row ${i}`));
    }

    return binaryMask;
}

// Decode from RLE to Uint8Array mask
export function decodeMask(size: [number, number], counts: number[]): Uint8Array {
    const mask = new Uint8Array(size[0] * size[1]);

    let p = 0;
    let zeros = 0;
    let ones = 0;

    for (let i = 0; i < counts.length; i++) {
        let count = counts[i];

        if (zeros + ones + count > mask.length) {
            break;
        }

        if (i % 2 === 0) {
            zeros += count;
        } else {
            ones += count;

            while (count > 0) {
                mask[p++] = 1;
                count--;
            }
        }
    }

    return mask;
}

/**
 * Decode RLE counts into a Uint8Array
 * @param rows number of rows
 * @param cols number of columns
 * @param counts RLE encoded counts
 * @returns Uint8Array representing the binary mask
 */
export function decodeRleCounts([rows, cols]: [number, number], counts: number[]): Uint8Array {
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
}
