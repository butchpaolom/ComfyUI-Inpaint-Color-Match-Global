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
                "sample_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("corrected_image",)
    FUNCTION = "match_color_with_mask"
    CATEGORY = "image/color_correction"

    def match_color_with_mask(self, original_image, edited_image, sample_mask):
        # Determine the smallest batch size across all inputs for safe processing
        batch_size = min(original_image.shape[0], edited_image.shape[0], sample_mask.shape[0])
        out_images = []

        for i in range(batch_size):
            # 1. Convert PyTorch tensor to numpy array and scale to 0-255
            orig_np = (original_image[i].cpu().numpy() * 255.0).astype(np.uint8)
            edit_np = (edited_image[i].cpu().numpy() * 255.0).astype(np.uint8)
            
            # Handle the mask batch. If there's only one mask, reuse it for all images.
            current_mask = sample_mask[i] if sample_mask.shape[0] > 1 else sample_mask[0]
            current_mask_np = current_mask.cpu().numpy()
            
            # Safety check: Ensure mask dimensions match the image dimensions
            img_h, img_w, _ = orig_np.shape
            mask_h, mask_w = current_mask_np.shape
            if mask_h != img_h or mask_w != img_w:
                print(f"Warning: Mask dimensions ({mask_h}x{mask_w}) do not match image dimensions ({img_h}x{img_w}). Resizing mask.")
                current_mask_np = cv2.resize(current_mask_np, (img_w, img_h), interpolation=cv2.INTER_AREA)

            # 2. Convert mask to binary. We consider any value above 0.5 as "in the mask"
            binary_mask = (current_mask_np > 0.5)

            # Safety check: If the mask is empty, pass through the edited image
            if not np.any(binary_mask):
                print(f"Warning: Empty mask for image {i}. Passing through edited image.")
                out_images.append(edited_image[i])
                continue

            # 3. Convert from RGB to LAB color space
            orig_lab = cv2.cvtColor(orig_np, cv2.COLOR_RGB2LAB).astype(np.float32)
            edit_lab = cv2.cvtColor(edit_np, cv2.COLOR_RGB2LAB).astype(np.float32)

            # 4. Extract only the pixels from the masked region for statistical calculation
            orig_sample_values = orig_lab[binary_mask]
            edit_sample_values = edit_lab[binary_mask]

            # 5. Calculate Mean and Standard Deviation of the masked region for each channel
            # NumPy's mean and std work efficiently on the extracted pixel values.
            orig_means_masked = np.mean(orig_sample_values, axis=0)
            orig_stds_masked = np.std(orig_sample_values, axis=0)
            edit_means_masked = np.mean(edit_sample_values, axis=0)
            edit_stds_masked = np.std(edit_sample_values, axis=0)

            # 6. Apply global adjustments to the ENTIRE edited image based on masked stats
            result_lab = np.zeros_like(edit_lab)

            for c in range(3):
                # Calculate Contrast/Saturation ratio (prevent division by zero)
                std_ratio = orig_stds_masked[c] / (edit_stds_masked[c] + 1e-5)
                
                # Apply Reinhard transfer formula to the full image channel
                channel_full = (edit_lab[:, :, c] - edit_means_masked[c]) * std_ratio + orig_means_masked[c]
                result_lab[:, :, c] = np.clip(channel_full, 0, 255)

            # 7. Convert back to RGB, scale back to 0.0-1.0, and convert back to Tensor
            result_rgb = cv2.cvtColor(result_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
            result_tensor = torch.from_numpy(result_rgb.astype(np.float32) / 255.0)
            
            out_images.append(result_tensor)

        # 8. Stack all processed images in the batch back into a single tensor
        if not out_images: # Handle empty output edge case
             return (edited_image,)
             
        return (torch.stack(out_images),)
