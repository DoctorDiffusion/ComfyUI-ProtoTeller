# ComfyUI-ProtoTeller
Custom ComfyUI nodes for a tarot card reader workflow.

Install to ComfyUI custom_nodes folder.

## Model Links

**Diffusion Model**

- [z_image_bf16.safetensors](https://huggingface.co/Comfy-Org/z_image/resolve/main/split_files/diffusion_models/z_image_bf16.safetensors)

**Text Encoders**

- [gemma_3_12B_it_fp8_scaled.safetensors](https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp8_scaled.safetensors)
- [qwen_3_4b.safetensors](https://huggingface.co/Comfy-Org/z_image/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors)

**LoRAs**

- [PNTE_neg_ZiT_A_v1.safetensors](https://huggingface.co/DoctorDiffusion/Z-Image-Turbo-PNTE-Negative-LoRA/resolve/main/PNTE_neg_ZiT_A_v1.safetensors)
- [trtcrd_zimage_dedistilled_lora_v001.safetensors](https://civitai.com/api/download/models/2815759?type=Model&format=SafeTensor)

**VAE**
- [ae.safetensors](https://huggingface.co/Comfy-Org/z_image/resolve/main/split_files/vae/ae.safetensors)


## Model Storage Location

```
📂 ComfyUI/
├── 📂 models/
│   ├── 📂 diffusion_models/
│   │   └── z_image_turbo_bf16.safetensors
│   ├── 📂 clip/
│   │   ├── gemma_3_12B_it_fp8_scaled.safetensors
│   │   └── qwen_3_4b.safetensors
│   ├── 📂 loras/
│   │   ├── PNTE_neg_ZiT_A_v1.safetensors
│   │   └── trtcrd_zimage_dedistilled_lora_v001.safetensors
│   └── 📂 vae/
│       └── ae.safetensors
├── 📂 custom_nodes/
│   ├── 📂 ComfyUI-ProtoTeller/
```
