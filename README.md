ComfyUI Masked Global Color Shift

This is a custom node for ComfyUI that helps fix color shifts in your images using a specific reference area. 

Instead of doing a heavy overhaul that ruins your contrast, this node just looks at a masked area, figures out the color difference (like a quick white balance or tint adjustment) between your original photo and the edited one, and applies that exact color tweak to your whole canvas. Think of it like snapping a subtle colored gel over a camera lens to fix weird AI color casts while keeping your original lighting completely untouched.

What It Does

* Samples locally, fixes globally: You mask a specific spot (like a face or a wall) to check the colors, but the color correction applies to the entire image.
* Protects your lighting: It uses a simple linear shift in the LAB color space, meaning it just adds or subtracts color values without messing up your hard-earned shadows, midtones, or highlights.
* Auto-resizes masks: Don't worry if your mask isn't the exact same dimensions as your image; the node scales it for you automatically.
* Chill failsafe: If you accidentally pass an empty mask, it won't crash your workflow. It just passes the edited image straight through.

How to Install

1. Open your terminal and navigate to your ComfyUI custom_nodes folder.
2. Clone the repository:
   git clone https://github.com/butchpaolom/ComfyUI-Inpaint-Color-Match-Global.git
3. Restart ComfyUI. You'll find the node waiting for you in the image/color_correction category.

Node Inputs & Outputs

* original_image (Input): Your baseline image that has the nice, correct colors you want to keep.
* edited_image (Input): The AI-generated image that needs a little color help.
* inverted_mask (Input): Inverted mask of the inpainted area.
* shifted_image (Output): Your final image, globally color-corrected.
