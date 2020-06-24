import torch
import torch.backends.cudnn as cudnn
import numpy as np
import PIL.Image as pil_image
import cv2
import time
from models import ESPCN
from utils import convert_ycbcr_to_rgb, preprocess, calc_psnr
import matplotlib.pyplot as plt


class Enhancer:
    def __init__(self):
        self.scale = 3
        self.weights_file = 'espcn_x3.pth'

        cudnn.benchmark = True
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

        self.model = ESPCN(scale_factor=self.scale).to(self.device)

        state_dict = self.model.state_dict()

        for n, p in torch.load(self.weights_file, map_location=lambda storage, loc: storage).items():
            if n in state_dict.keys():
                state_dict[n].copy_(p)
            else:
                raise KeyError(n)

        self.model.eval()

    def enhance(self, frame):
        first = time.time()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # frame = np.array(frame) / 255.

        bicubic = cv2.resize(frame, dsize=(frame.shape[1] * self.scale, frame.shape[0] * self.scale),
                             interpolation=cv2.INTER_CUBIC)
        frame = torch.tensor(frame).to(self.device)

        bicubic = torch.tensor(bicubic).to(self.device)
        _, ycbcr = preprocess(bicubic, self.device)
        lr, _ = preprocess(frame, self.device)

        with torch.no_grad():
            preds = self.model(lr).clamp(0.0, 1.0)

        preds = torch.squeeze(preds.mul(255.0))#.cpu().numpy().squeeze(0).squeeze(0)
        # print('preds:',preds.shape)
        # print('ycbcr:',ycbcr.shape)

        output = torch.stack([preds, ycbcr[..., 1], ycbcr[..., 2]]).permute([1, 2, 0])
        output = torch.clamp(convert_ycbcr_to_rgb(output), 0.0, 255.0).cpu().numpy().astype(np.uint8)

        return output
