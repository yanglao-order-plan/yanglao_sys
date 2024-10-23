import fire

from work_flow.utils.sahi.predict import predict


def main():
    fire.Fire(predict)


if __name__ == "__main__":
    main()
