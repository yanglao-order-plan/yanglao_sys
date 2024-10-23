/**
 * Custom mask tracing algorithm
 *  1. Find the "breakpoints" (endpoints of every filled block) of every line in the image
 *  2. For each pair of lines, greedily connect every pair of endpoints ordered from top to bottom
 *       - Connect short horizontal segments into long ones where possible
 *       - Convert diagonal segments into horizontal/vertical segment pairs to make right angles where reasonable
 *       - Add segments to close polygons
 *  3. Repeatedly choose vertices and follow adjacent ones to create joined SVG path data strings.
 *       - Choose the next unused point (in sorted order by x, y)
 *       - Repeatedly choose adjacent vertices until the path is closed
 *           - The vertices are necessarily sorted in counter-clockwise order
 *             due how the edges were generated in step 2
 *       - Check how many existing paths this point is inside, and reverse the order of points if necessary
 *       - Convert path to an SVG string and add to final output
 */

/**
 * Helper function
 * Converts string representation of point (used as Map key) back into [x, y] array
 * @param {str} point "x y"
 * @returns {Array<number>} [x, y]
 */
const splitPointKey = (point: string): number[] => {
    return point.split(" ").map((a) => parseInt(a));
};

// Interface for a Breakpoint
interface Breakpoint {
    line: number;
    points: number[];
}
/**
 * Used in generatePolygonSegments
 * ------
 * Step 1
 * ------
 * Converts a mask encoded with RLE and converts it into an array of breakpoints per column of the mask.
 *     - Each line starts as 0 by default, and at each breakpoint the bit is flipped
 *     - If a line doesn't exist in the return array, this line is all 0.
 *
 * @param {Array<number>} rleMask
 * @param {number} height (of mask)
 * @returns {Array<Object>} each item is a JS object describing the breakpoints for a line:
 *    {
 *        line {number}: index of line this object describes,
 *        points {Array<number>}: list of pixel indices along line at which bit goes from 0 -> 1 or vice versa
 *    }
 */
const getLineBreakpoints = (rleMask: number[], height: number): Breakpoint[] => {
    const breakpoints: Breakpoint[] = [];
    const currentLine: Breakpoint = { line: -1, points: [] };
    let sum = 0; // sum of pixels seen so far, used to compute breakpoints

    // Helper function to push currentLine data to breakpoints
    const addCurrentLineToBreakpoints = (): void => {
        if (currentLine.points.length > 0) {
            breakpoints.push({ line: currentLine.line, points: [...currentLine.points] });
            currentLine.points = [];
        }
    };

    // Iterate through every pair of values in rleMask
    for (let i = 1; i < rleMask.length; i += 2) {
        // Get coords of start/end pixels of the filled block
        sum += rleMask[i - 1];
        const y1 = sum % height;
        const x1 = Math.floor(sum / height);

        sum += rleMask[i];
        const y2 = sum % height;
        const x2 = Math.floor(sum / height);

        if (currentLine.line !== x1) {
            addCurrentLineToBreakpoints();
            currentLine.line = x1;
        }
        // Case if the block is just one line
        if (x1 === x2) {
            currentLine.points.push(y1, y2);
            continue;
        }
        // Otherwise, first handle the first line of the block
        currentLine.points.push(y1, height);
        addCurrentLineToBreakpoints();
        currentLine.line = x2;
        // Then handle in-between lines, which are all filled
        for (let x0 = x1 + 1; x0 < x2; x0++) {
            breakpoints.push({ line: x0, points: [0, height] });
        }
        // Lastly, handle the last line of the block
        if (y2 > 0) {
            currentLine.points.push(0, y2);
        }
    }
    // Push any remaining data in currentLine to breakpoints
    addCurrentLineToBreakpoints();

    return breakpoints;
};
// Interface for a Point
interface Point {
    x: number;
    y: number;
}
// Type alias for PolySegments
type PolySegments = Map<string, Set<string>>;
/**
 * ------
 * Step 2
 * ------
 * Generates a Map of segments that collectively trace all EDGES within a mask.
 *
 * @param {Array<number>} rleMask
 * @param {number} height (of mask)
 * @returns {Map<string, Set<string>>} Map of all vertices to its adjacent vertices
 *    - key: "x y" string-formatted point
 *    - value: Set of string-formatted points adjacent to key
 */
const generatePolygonSegments = (rleMask: number[], height: number): PolySegments => {
    const breakpoints = getLineBreakpoints(rleMask, height);

    if (breakpoints.length === 0) return new Map();

    const polySegments: PolySegments = new Map();
    let lastLine = -1;
    let lastPoints: number[] = [];
    const horizontalSegments: Map<number, number> = new Map();

    const addToPolySegments = (p1: Point, p2: Point): void => {
        const p1Str = `${p1.x} ${p1.y}`;
        const p2Str = `${p2.x} ${p2.y}`;
        if (!polySegments.has(p1Str)) polySegments.set(p1Str, new Set());
        polySegments.get(p1Str)!.add(p2Str);
        if (!polySegments.has(p2Str)) polySegments.set(p2Str, new Set());
        polySegments.get(p2Str)!.add(p1Str);
    };

    const closeHorizontalSegment = (y: number, x2: number): void => {
        if (x2 !== horizontalSegments.get(y)) {
            addToPolySegments({ x: horizontalSegments.get(y)!, y }, { x: x2, y });
            horizontalSegments.delete(y);
        }
    };

    const addSegment = (x1: number, y1: number, x2: number, y2: number): void => {
        if (y1 === y2) {
            if (!horizontalSegments.has(y1)) horizontalSegments.set(y1, x1);
            return;
        }
        let canStraighten = false;
        const maxX = Math.max(x1, x2);
        if (horizontalSegments.has(y1)) {
            closeHorizontalSegment(y1, maxX);
            canStraighten = true;
        }
        if (horizontalSegments.has(y2)) {
            closeHorizontalSegment(y2, maxX);
            canStraighten = true;
        }
        if (canStraighten) {
            addToPolySegments({ x: maxX, y: y1 }, { x: maxX, y: y2 });
        } else {
            addToPolySegments({ x: x1, y: y1 }, { x: x2, y: y2 });
        }
    };

    const closePreviousLine = (prevLine: number, prevPoints: number[]): void => {
        for (const y of prevPoints) {
            addSegment(prevLine, y, prevLine + 1, y);
        }
        for (let i = 1; i < prevPoints.length; i += 2) {
            addSegment(prevLine + 1, prevPoints[i - 1], prevLine + 1, prevPoints[i]);
        }
    };

    for (const { line, points } of breakpoints) {
        if (line !== lastLine + 1) {
            closePreviousLine(lastLine, lastPoints);
            lastLine = line - 1;
            lastPoints = [];
        }
        let x1 = lastPoints.length && lastPoints[0] <= points[0] ? lastLine : line;
        let y1 = x1 === lastLine ? lastPoints[0] : points[0];
        let lastLineIndex = x1 === lastLine ? 1 : 0;
        let newLineIndex = x1 === lastLine ? 0 : 1;
        let odd = true;
        while (lastLineIndex < lastPoints.length || newLineIndex < points.length) {
            let x2, y2;
            if (lastLineIndex === lastPoints.length || points[newLineIndex] < lastPoints[lastLineIndex]) {
                x2 = line;
                y2 = points[newLineIndex];
                newLineIndex++;
            } else {
                x2 = lastLine;
                y2 = lastPoints[lastLineIndex];
                lastLineIndex++;
            }
            if (odd) {
                if (x1 === lastLine && x2 === lastLine) {
                    addSegment(lastLine, y1, line, y1);
                    addSegment(lastLine, y2, line, y2);
                    addSegment(line, y1, line, y2);
                } else {
                    addSegment(x1, y1, x2, y2);
                }
            }
            odd = !odd;
            x1 = x2;
            y1 = y2;
        }
        lastLine = line;
        lastPoints = points;
    }
    closePreviousLine(lastLine, lastPoints);

    const sortedSegments: PolySegments = new Map(
        Array.from(polySegments.entries()).sort(([keyA], [keyB]) => {
            const [x1, y1] = splitPointKey(keyA);
            const [x2, y2] = splitPointKey(keyB);
            if (x1 === x2) return y1 - y2;
            return x1 - x2;
        })
    );

    return sortedSegments;
};

/**
 * ------
 * Step 3
 * ------
 * Converts Map of segments from generatePolygonSegments into closed SVG paths combined into one string,
 * where nested paths alternate direction so holes are correctly rendered using the nonzero fill rule.
 * @param {Map<string, Set<string>>} polySegments output of generatePolygonSegments
 * @returns {string} SVG data string for display
 */
export const convertSegmentsToSVG = (polySegments: PolySegments): string[] => {
    const paths: number[][][] = [];
    while (polySegments.size) {
        let [point, targets] = polySegments.entries().next().value as [string, Set<string>];
        const firstPoint = point;
        const path: number[][] = [splitPointKey(firstPoint)];
        let nextPoint: string | null = null;
        while (nextPoint !== firstPoint) {
            // 确保 nextPoint 不是 null
            if (nextPoint !== null) {
                path.push(splitPointKey(nextPoint));
                targets.delete(nextPoint);
                if (targets.size === 0) polySegments.delete(point);
            }
            // 添加 null 检查以避免类型错误
            const nextPointTargets = nextPoint !== null ? polySegments.get(nextPoint) : null;
            if (nextPointTargets) {
                nextPointTargets.delete(point);
                if (nextPointTargets.size === 0) {
                    polySegments.delete(nextPoint!); // 使用非空断言操作符
                    break;
                } else {
                    if (nextPoint !== null) { // 添加 null 检查
                        point = nextPoint;
                        targets = nextPointTargets;
                    }
                }
            } else {
                break; // 如果 nextPointTargets 为 null，退出循环
            }
        }
        paths.push(path);
    }

    const renderedPaths: Path2D[] = [];
    const svgStrings: string[] = [];
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    for (const path of paths) {
        let shouldBeClockwise = false;
        const [sampleX, sampleY] = path[0];
        for (const otherPath of renderedPaths) {
            if (ctx && ctx.isPointInPath(otherPath, sampleX + 0.5, sampleY + 0.5)) {
                shouldBeClockwise = !shouldBeClockwise;
            }
        }
        if (shouldBeClockwise) path.reverse();

        const stringPoints = path.slice(1).map(([x, y]) => `${x} ${y}`).join(" ");
        const svgStr = `M${path[0][0]} ${path[0][1]} L` + stringPoints;
        svgStrings.push(svgStr);

        const pathObj = new Path2D(svgStr);
        ctx!.fill(pathObj);
        renderedPaths.push(pathObj);
    }

    return svgStrings;
};
