# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/07_tta.ipynb (unless otherwise specified).

__all__ = ['rot90', 'hflip', 'vflip', 'BaseTransform', 'Chain', 'Transformer', 'Compose', 'Merger', 'HorizontalFlip',
           'VerticalFlip', 'Rotate90']

# Cell
import torch
import itertools
from functools import partial
from typing import List, Optional, Union
from fastcore.foundation import store_attr

# Cell
def rot90(x, k=1):
    "rotate batch of images by 90 degrees k times"
    return torch.rot90(x, k, (2, 3))

def hflip(x):
    "flip batch of images horizontally"
    return x.flip(3)

def vflip(x):
    "flip batch of images vertically"
    return x.flip(2)

# Cell
class BaseTransform:
    identity_param = None
    def __init__(self, pname: str, params: Union[list, tuple]): store_attr()

class Chain:
    def __init__(self, functions: List[callable]):
        self.functions = functions or []

    def __call__(self, x):
        for f in self.functions:
            x = f(x)
        return x

class Transformer:
    def __init__(self, image_pipeline: Chain, mask_pipeline: Chain):
        store_attr()

    def augment_image(self, image):
        return self.image_pipeline(image)

    def deaugment_mask(self, mask):
        return self.mask_pipeline(mask)

class Compose:
    def __init__(self, aug_transforms: List[BaseTransform]):
        store_attr()
        self.aug_transform_parameters = list(itertools.product(*[t.params for t in self.aug_transforms]))
        self.deaug_transforms = aug_transforms[::-1]
        self.deaug_transform_parameters = [p[::-1] for p in self.aug_transform_parameters]

    def __iter__(self) -> Transformer:
        for aug_params, deaug_params in zip(self.aug_transform_parameters, self.deaug_transform_parameters):
            image_aug_chain = Chain([partial(t.apply_aug_image, **{t.pname: p})
                                     for t, p in zip(self.aug_transforms, aug_params)])
            mask_deaug_chain = Chain([partial(t.apply_deaug_mask, **{t.pname: p})
                                      for t, p in zip(self.deaug_transforms, deaug_params)])
            yield Transformer(image_pipeline=image_aug_chain, mask_pipeline=mask_deaug_chain)

    def __len__(self) -> int:
        return len(self.aug_transform_parameters)

# Cell
class Merger:
    def __init__(self):
        self.output = []

    def append(self, x):
        self.output.append(torch.as_tensor(x))

    def result(self, type='mean'):
        s = torch.stack(self.output)
        if type == 'max':
            result = torch.max(s, dim=0)[0]
        elif type == 'mean':
            result = torch.mean(s, dim=0)
        elif type ==  'std':
            result = torch.std(s, dim=0)
        else:
            raise ValueError('Not correct merge type `{}`.'.format(self.type))
        return result

# Cell
class HorizontalFlip(BaseTransform):
    "Flip images horizontally (left->right)"
    identity_param = False
    def __init__(self):
        super().__init__("apply", [False, True])

    def apply_aug_image(self, image, apply=False, **kwargs):
        if apply: image = hflip(image)
        return image

    def apply_deaug_mask(self, mask, apply=False, **kwargs):
        if apply: mask = hflip(mask)
        return mask

# Cell
class VerticalFlip(BaseTransform):
    "Flip images vertically (up->down)"
    identity_param = False
    def __init__(self):
        super().__init__("apply", [False, True])

    def apply_aug_image(self, image, apply=False, **kwargs):
        if apply: image = vflip(image)
        return image

    def apply_deaug_mask(self, mask, apply=False, **kwargs):
        if apply: mask = vflip(mask)
        return mask

# Cell
class Rotate90(BaseTransform):
    "Rotate images 0/90/180/270 degrees (`angles`)"
    identity_param = 0
    def __init__(self, angles: List[int]):
        if self.identity_param not in angles:
            angles = [self.identity_param] + list(angles)
        super().__init__("angle", angles)

    def apply_aug_image(self, image, angle=0, **kwargs):
        k = angle // 90 if angle >= 0 else (angle + 360) // 90
        return rot90(image, k)

    def apply_deaug_mask(self, mask, angle=0, **kwargs):
        return self.apply_aug_image(mask, -angle)