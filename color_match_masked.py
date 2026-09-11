import torch
import numpy as np
import cv2

class MaskedGlobalColorMatchNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "original_image": ("IMAGE",),
                "edited_image": ("IMAGE",),
                "inverted_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("shifted_image",)
    FUNCTION = "apply_global_shift"
    CATEGORY = "image/color_correction"

    def apply_global_shift(self, original_image, edited_image, inverted_mask):
        batch_size = min(original_image.shape[0], edited_image.shape[0], inverted_mask.shape[0])
        out_images = []

        for i in range(batch_size):
            # 1. Convert to numpy arrays
            orig_np = (original_image[i].cpu().numpy() * 255.0).astype(np.uint8)
            edit_np = (edited_image[i].cpu().numpy() * 255.0).astype(np.uint8)
            
            # Mask handling
            current_mask = inverted_mask[i] if inverted_mask.shape[0] > 1 else inverted_mask[0]
            current_mask_np = current_mask.cpu().numpy()
            
            img_h, img_w, _ = orig_np.shape
            mask_h, mask_w = current_mask_np.shape
            if mask_h != img_h or mask_w != img_w:
                current_mask_np = cv2.resize(current_mask_np, (img_w, img_h), interpolation=cv2.INTER_AREA)

            binary_mask = (current_mask_np > 0.5)

            if not np.any(binary_mask):
                out_images.append(edited_image[i])
                continue

            # 2. RGB to LAB conversion for natural-looking color shifts
            orig_lab = cv2.cvtColor(orig_np, cv2.COLOR_RGB2LAB).astype(np.float32)
            edit_lab = cv2.cvtColor(edit_np, cv2.COLOR_RGB2LAB).astype(np.float32)

            # 3. Extract only the masked pixels
            orig_sample = orig_lab[binary_mask]
            edit_sample = edit_lab[binary_mask]

            # 4. Calculate the average color of both masked regions
            orig_means = np.mean(orig_sample, axis=0)
            edit_means = np.mean(edit_sample, axis=0)
            
            # Calculate the mathematical difference (shift) between the two
            color_shift = orig_means - edit_means

            # 5. Apply this exact shift to the ENTIRE edited image
            result_lab = np.zeros_like(edit_lab)
            for c in range(3):
                # Add the color difference to all pixels globally
                channel_shifted = edit_lab[:, :, c] + color_shift[c]
                result_lab[:, :, c] = np.clip(channel_shifted, 0, 255)

            # 6. Convert back to RGB and tensor format
            result_rgb = cv2.cvtColor(result_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
            result_tensor = torch.from_numpy(result_rgb.astype(np.float32) / 255.0)
            
            out_images.append(result_tensor)

        return (torch.stack(out_images),)