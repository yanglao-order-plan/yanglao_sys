function throttle<T extends (...args: any[]) => void>(func: T, delay: number): (...args: Parameters<T>) => void {
    let timer: ReturnType<typeof setTimeout> | null = null; // 定时器变量

    return function (this: any, ...args: Parameters<T>) { // 添加 this 类型注释
        const context = this; // 保存 this 指向

        if (!timer) {
            timer = setTimeout(() => {
                func.apply(context, args); // 调用原始函数并传入上下文和参数
                if (timer) { // 确保 timer 不为 null
                    clearTimeout(timer); // 清除计时器
                }
                timer = null; // 重置计时器为 null
            }, delay);
        }
    };
}

export default throttle;
