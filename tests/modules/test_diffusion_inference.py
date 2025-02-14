# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.

import os
import unittest

import imageio
import numpy as np
import torchvision.transforms as TT
import torchvision.transforms.functional as TF
from PIL import Image
from torchvision.utils import save_image

from scepter.modules.annotator.registry import ANNOTATORS
from scepter.modules.inference.ace_inference import ACEInference
from scepter.modules.inference.diffusion_inference import DiffusionInference
from scepter.modules.inference.sd3_inference import SD3Inference
from scepter.modules.inference.flux_inference import FluxInference
from scepter.modules.inference.stylebooth_inference import StyleboothInference
from scepter.modules.inference.cogvideox_inference import CogVideoXInference
from scepter.modules.utils.config import Config
from scepter.modules.utils.distribute import we
from scepter.modules.utils.file_system import FS
from scepter.modules.utils.logger import get_logger
from torchvision.utils import save_image


class DiffusionInferenceTest(unittest.TestCase):
    def setUp(self):
        print(('Testing %s.%s' % (type(self).__name__, self._testMethodName)))
        self.logger = get_logger(name='scepter')
        config_file = 'scepter/methods/studio/scepter_ui.yaml'
        cfg = Config(cfg_file=config_file)
        if 'FILE_SYSTEM' in cfg:
            for fs_info in cfg['FILE_SYSTEM']:
                FS.init_fs_client(fs_info)
        self.tmp_dir = './cache/save_data/diffusion_inference'
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def tearDown(self):
        super().tearDown()

    @unittest.skip('')
    def test_sd15(self):
        config_file = 'scepter/methods/studio/inference/stable_diffusion/sd15_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        output = diff_infer({'prompt': 'a cute dog'})
        save_path = os.path.join(self.tmp_dir,
                                 'sd15_test_prompt_a_cute_dog.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sd21(self):
        config_file = 'scepter/methods/studio/inference/stable_diffusion/sd21_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        output = diff_infer({'prompt': 'a cute dog'})
        save_path = os.path.join(self.tmp_dir,
                                 'sd21_test_prompt_a_cute_dog.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sdxl(self):
        config_file = 'scepter/methods/studio/inference/sdxl/sdxl1.0_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        output = diff_infer({'prompt': 'a cute dog'})
        save_path = os.path.join(self.tmp_dir,
                                 'sdxl_test_prompt_a_cute_dog.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sd15_scedit_t2i_2D(self):
        # init model
        config_file = 'scepter/methods/studio/inference/stable_diffusion/sd15_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        # load tuner model
        tuner_model = {
            'NAME': 'Flat 2D Art',
            'NAME_ZH': None,
            'DESCRIPTION': None,
            'BASE_MODEL': 'SD1.5',
            'IMAGE_PATH': None,
            'TUNER_TYPE': 'SwiftSCE',
            'MODEL_PATH':
            'ms://iic/scepter_scedit@tuners_model/SD1.5/Flat2DArt',
            'PROMPT_EXAMPLE': None
        }
        tuner_model = Config(cfg_dict=tuner_model, load=False)
        # prepare data
        input_data = {'prompt': 'a single flower is shown in front of a tree'}
        input_params = {
            'tuner_model': tuner_model,
            'tuner_scale': 1.0,
            'seed': 2024
        }
        output = diff_infer(input_data, **input_params)
        save_path = os.path.join(self.tmp_dir, 'sd15_flower_2d.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sd21_scedit_ctr_canny(self):
        # init model
        config_file = 'scepter/methods/studio/inference/stable_diffusion/sd21_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        # extract condition
        canny_dict = {
            'NAME': 'CannyAnnotator',
            'LOW_THRESHOLD': 100,
            'HIGH_THRESHOLD': 200
        }
        canny_anno = Config(cfg_dict=canny_dict, load=False)
        canny_ins = ANNOTATORS.build(canny_anno).to(we.device_id)
        output_height, output_width = 768, 768
        control_cond_image = Image.open('asset/images/flower.jpg')
        control_cond_image = TT.Resize(min(output_height,
                                           output_width))(control_cond_image)
        control_cond_image = TT.CenterCrop(
            (output_height, output_width))(control_cond_image)
        control_cond_image = canny_ins(np.array(control_cond_image))
        control_save_path = os.path.join(self.tmp_dir,
                                         'sd21_flower_canny_preproccess.png')
        save_image(TF.to_tensor(control_cond_image), control_save_path)
        control_cond_image = Image.open(control_save_path)
        # load control model
        control_model = {
            'NAME':
            'canny',
            'NAME_ZH':
            None,
            'DESCRIPTION':
            None,
            'BASE_MODEL':
            'SD2.1',
            'TYPE':
            'Canny',
            'MODEL_PATH':
            'ms://iic/scepter_scedit@controllable_model/SD2.1/canny_control'
        }
        control_model = Config(cfg_dict=control_model, load=False)
        # prepare data
        input_data = {'prompt': 'a single flower is shown in front of a tree'}
        input_params = {
            'control_model': control_model,
            'control_cond_image': control_cond_image,
            'control_scale': 1.0,
            'crop_type': 'CenterCrop',
            'seed': 2024
        }
        output = diff_infer(input_data, **input_params)
        save_path = os.path.join(self.tmp_dir, 'sd21_flower_canny.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sdxl_scedit_ctr_canny(self):
        # init model
        config_file = 'scepter/methods/studio/inference/sdxl/sdxl1.0_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = DiffusionInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        # extract condition
        canny_dict = {
            'NAME': 'CannyAnnotator',
            'LOW_THRESHOLD': 100,
            'HIGH_THRESHOLD': 200
        }
        canny_anno = Config(cfg_dict=canny_dict, load=False)
        canny_ins = ANNOTATORS.build(canny_anno).to(we.device_id)
        output_height, output_width = 1024, 1024
        control_cond_image = Image.open('asset/images/flower.jpg')
        control_cond_image = TT.Resize(min(output_height,
                                           output_width))(control_cond_image)
        control_cond_image = TT.CenterCrop(
            (output_height, output_width))(control_cond_image)
        control_cond_image = canny_ins(np.array(control_cond_image))
        control_save_path = os.path.join(self.tmp_dir,
                                         'sdxl_flower_canny_preproccess.png')
        save_image(TF.to_tensor(control_cond_image), control_save_path)
        control_cond_image = Image.open(control_save_path)
        # load control model
        control_model = {
            'NAME':
            'canny',
            'NAME_ZH':
            None,
            'DESCRIPTION':
            None,
            'BASE_MODEL':
            'SD_XL1.0',
            'TYPE':
            'Canny',
            'MODEL_PATH':
            'ms://iic/scepter_scedit@controllable_model/SD_XL1.0/canny_control'
        }
        control_model = Config(cfg_dict=control_model, load=False)
        # prepare data
        input_data = {'prompt': 'a single flower is shown in front of a tree'}
        input_params = {
            'control_model': control_model,
            'control_cond_image': control_cond_image,
            'control_scale': 1.0,
            'crop_type': 'CenterCrop',
            'seed': 2024
        }
        output = diff_infer(input_data, **input_params)
        save_path = os.path.join(self.tmp_dir, 'sdxl_flower_canny.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_stylebooth(self):
        config_file = 'scepter/methods/studio/inference/edit/stylebooth_tb_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = StyleboothInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)

        output = diff_infer(
            {'prompt': 'Let this image be in the style of sai-lowpoly'},
            style_edit_image=Image.open(
                'asset/images/inpainting_text_ref/ex4_scene_im.jpg'),
            style_guide_scale_text=7.5,
            style_guide_scale_image=1.5)
        save_path = os.path.join(self.tmp_dir,
                                 'stylebooth_test_lowpoly_cute_dog.png')
        save_image(output['images'], save_path)

    @unittest.skip('')
    def test_sd3(self):
        config_file = 'scepter/methods/studio/inference/dit/sd3_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = SD3Inference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        input_params = {
            'seed': 2024
        }
        output = diff_infer({
            'prompt': 'a cat holds a blackboard that writes "hello world"'
        }, **input_params)
        save_path = os.path.join(self.tmp_dir, 'sd3_cat.png')
        save_image(output['images'], save_path)
        print(save_path)

    @unittest.skip('')
    def test_flux(self):
        config_file = 'scepter/methods/studio/inference/dit/flux1.0_dev_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = FluxInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        input_params = {
            'seed': 2024
        }
        output = diff_infer({
            'prompt': '1 girl'
        }, **input_params)
        save_path = os.path.join(self.tmp_dir, 'flux_dev_1girl.png')
        save_image(output['images'], save_path)
        print(save_path)

    @unittest.skip('')
    def test_ace(self):
        config_file = 'scepter/methods/studio/chatbot/models/ace_0.6b_512.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = ACEInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        output = diff_infer(prompt='1 girl', seed=2024)
        save_path = os.path.join(self.tmp_dir, 'ace_1girl.png')
        output[0].save(save_path, format='PNG')
        print(save_path)


    @unittest.skip('')
    def test_cogvideox_2b(self):
        config_file = 'scepter/methods/studio/inference/dit/cogvideox_2b_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = CogVideoXInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        input_params = {
            'seed': 42
        }
        output = diff_infer({
            'prompt': 'A girl riding a bike.'
        }, **input_params)
        frames = (output['videos'][0].permute(1, 2, 3, 0).cpu().numpy() * 255).astype(np.uint8)
        save_path = os.path.join(self.tmp_dir, 'cogvideox_2b_girlbike.mp4')
        writer = imageio.get_writer(save_path, fps=8)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
        print(save_path)

    # @unittest.skip('')
    def test_cogvideox_5b(self):
        config_file = 'scepter/methods/studio/inference/dit/cogvideox_5b_pro.yaml'
        cfg = Config(cfg_file=config_file)
        diff_infer = CogVideoXInference(logger=self.logger)
        diff_infer.init_from_cfg(cfg)
        input_params = {
            'seed': 42
        }
        output = diff_infer({
            'prompt': 'A girl riding a bike.'
        }, **input_params)
        frames = (output['videos'][0].permute(1, 2, 3, 0).cpu().numpy() * 255).astype(np.uint8)
        save_path = os.path.join(self.tmp_dir, 'cogvideox_5b_girlbike.mp4')
        writer = imageio.get_writer(save_path, fps=8)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()
        print(save_path)


if __name__ == '__main__':
    unittest.main()
