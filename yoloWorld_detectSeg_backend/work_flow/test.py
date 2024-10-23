from engines.model_manager import ModelManager

model_manager = ModelManager()
cfg = model_manager.get_model_configs()

def test_print(params):
    print(params)

def test_model_load():
    config_path = cfg[14]["config_file"]
    # for i in range(len(cfg)):
    #     if cfg[i]["name"] == 'groundingdino_swinb_attn_fuse_sam_hq_vit_l_quant':
    #         print(i)
    model_manager.load_model(config_path)
    model_manager.new_model_status.connect(lambda params: test_print(params))
    model_manager.model_loaded.connect(lambda params: test_print(params))
    # model_manager.model_configs_changed.connect(lambda params: test_print(params))


def test_infer():
    model_manager.predict_shapes_threading("E:\models\yanglao\data\images\1.jpg", "1.jpg")
    return


if __name__ == "__main__":
    print(cfg)
    # test_model_load()
