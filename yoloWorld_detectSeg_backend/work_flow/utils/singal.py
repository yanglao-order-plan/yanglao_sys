import threading


class AutoSignal:
    """
    一个扩展的自动任务队列类，具有以下功能：
    - 自动标记任务完成。
    - 可以在创建时指定装载对象的类型。
    - 提供类似信号的机制，以便更好地集成到事件驱动的应用中。
    """

    def __init__(self, *args, **kwargs):
        self.item_type = []  # 指定任务队列中项目的类型，类型可选
        for arg in args:
            if arg is not None and not isinstance(arg, type):
                raise TypeError("item_type must be a valid type or None.")
            else:
                self.item_type.append(arg)
        self._new_item_callbacks = []  # 存储新任务放入时的回调函数
        self._task_done_callbacks = []  # 存储任务完成时的回调函数
        self._callbacks = []  # 任务完成时的所有回调函数
        self._lock = threading.Lock()  # 确保线程安全

    def connect(self, callback):
        """
        连接一个回调函数，当信号发射时调用此函数。
        """
        with self._lock:
            self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        """
        异步调用连接的回调函数，将任务放入队列后，立即标记该任务为已完成。
        """
        items = []
        for i, arg in enumerate(args):
            tp = self.item_type[i] if i < len(self.item_type) else None
            if tp is not None and not isinstance(arg, tp):
                raise TypeError(f"Expected item of type {tp.__name__}, but got {type(arg).__name__}")
            else:
                items.append(arg)
        items = tuple(items) if len(items) > 1 else items[0]

        def _run_callbacks():
            with self._lock:
                for callback in self._callbacks:
                    callback(items)

        # 使用线程来异步执行所有回调函数
        threading.Thread(target=_run_callbacks).start()