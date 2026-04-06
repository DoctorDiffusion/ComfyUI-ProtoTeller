import torch
import numpy as np
import os
import re
import time
import random
from PIL import Image
import folder_paths


class ConditionalImageRotate:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "number": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "conditional_rotate"
    CATEGORY = "ProtoTeller"

    def conditional_rotate(self, image, number):
        image_np = image.cpu().numpy().squeeze()
        if number % 2 == 0:
            image_np = np.flipud(image_np)
        image_tensor = torch.from_numpy(image_np.copy()).unsqueeze(0)
        return (image_tensor,)


class ConditionalTextConcat:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_a": ("STRING", {"default": "", "multiline": True}),
                "text_b": ("STRING", {"default": "", "multiline": True}),
                "number": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "conditional_concat"
    CATEGORY = "ProtoTeller"

    def conditional_concat(self, text_a, text_b, number):
        if number % 2 == 0:
            return (text_a + text_b,)
        else:
            return (text_a,)


class PreviewTextImage:
    OUTPUT_DIR = os.path.join(folder_paths.get_output_directory(), "ProtoTeller")

    def __init__(self):
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "text": ("STRING", {"default": "", "multiline": True}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "preview"
    CATEGORY = "ProtoTeller"
    OUTPUT_NODE = True

    def preview(self, image, text):
        timestamp = int(time.time())
        base_name = f"cardreading_{timestamp}"
        png_filename = f"{base_name}.png"
        txt_filename = f"{base_name}.txt"

        png_path = os.path.join(self.OUTPUT_DIR, png_filename)
        txt_path = os.path.join(self.OUTPUT_DIR, txt_filename)

        # Save image
        image_np = image.cpu().numpy().squeeze()
        image_np = (image_np * 255).clip(0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np)
        pil_image.save(png_path)

        # Save text
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        return {
            "ui": {
                "images": [
                    {
                        "filename": png_filename,
                        "subfolder": "ProtoTeller",
                        "type": self.type,
                    }
                ],
                "text": [text],
            }
        }


class ConditionalTextSwitch:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_odd": ("STRING", {"default": "", "multiline": True}),
                "text_even": ("STRING", {"default": "", "multiline": True}),
                "number": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "conditional_switch"
    CATEGORY = "ProtoTeller"

    def conditional_switch(self, text_odd, text_even, number):
        if number % 2 != 0:
            return (text_odd,)
        else:
            return (text_even,)


class DrawWildcards:
    """
    Resolves wildcard tags in up to three separate text inputs and outputs
    each resolved string independently. Wildcards use the standard __name__
    syntax and are loaded from .txt files in the Impact Pack wildcards folder
    as well as ComfyUI's custom_wildcards path if configured.
    """

    # Wildcards are loaded from the ProtoTeller-local wildcards folder.
    # Drop your own .txt files in there to extend the available wildcards.
    _LOCAL_WILDCARDS = os.path.join(os.path.dirname(__file__), "wildcards")

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_1": ("STRING", {"default": "", "multiline": True}),
                "text_2": ("STRING", {"default": "", "multiline": True}),
                "text_3": ("STRING", {"default": "", "multiline": True}),
                "seed":   ("INT",    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("text_1", "text_2", "text_3")
    FUNCTION = "draw_wildcards"
    CATEGORY = "ProtoTeller"

    # ------------------------------------------------------------------
    # Wildcard loading
    # ------------------------------------------------------------------

    @classmethod
    def _load_wildcards(cls):
        """Return a dict mapping normalised wildcard key -> list of options."""
        wildcard_dict = {}

        search_paths = []
        if os.path.isdir(cls._LOCAL_WILDCARDS):
            search_paths.append(cls._LOCAL_WILDCARDS)

        for base in search_paths:
            for root, _dirs, files in os.walk(base, followlinks=True):
                for fname in files:
                    if not fname.endswith(".txt"):
                        continue
                    fpath = os.path.join(root, fname)
                    rel   = os.path.relpath(fpath, base)
                    key   = os.path.splitext(rel)[0].replace("\\", "/").replace(" ", "-").lower()
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            lines = [
                                ln.strip() for ln in fh
                                if ln.strip() and not ln.strip().startswith("#")
                            ]
                        if lines:
                            wildcard_dict[key] = lines
                    except OSError:
                        pass

        return wildcard_dict

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    @classmethod
    def _resolve(cls, text, wildcard_dict, rng):
        """
        Repeatedly expand __wildcard__ tags and {a|b|c} choice blocks
        until none remain (or a safety limit is hit).
        """
        for _ in range(100):  # safety cap on recursion depth
            new_text, changed = cls._expand_once(text, wildcard_dict, rng)
            if not changed:
                break
            text = new_text
        return text

    @staticmethod
    def _expand_once(text, wildcard_dict, rng):
        changed = False

        # 1. Resolve {option1|option2|...} blocks
        def replace_choice(m):
            nonlocal changed
            changed = True
            return rng.choice(m.group(1).split("|"))

        text = re.sub(r"\{([^{}]+?)\}", replace_choice, text)

        # 2. Resolve __wildcard__ tags
        def replace_wildcard(m):
            nonlocal changed
            key = m.group(1).lower().replace("\\", "/").replace(" ", "-")
            options = wildcard_dict.get(key)
            if options:
                changed = True
                return rng.choice(options)
            # Return the original tag untouched if key not found
            return m.group(0)

        text = re.sub(r"__([\w.\-+/*\\]+?)__", replace_wildcard, text)

        return text, changed

    def draw_wildcards(self, text_1, text_2, text_3, seed):
        rng = random.Random(seed)

        # Wrap choice so it accepts a list (mirrors numpy-style interface)
        rng.choice = lambda seq: random.Random(seed).choice(seq) if not seq else rng.choice.__func__(rng, seq)

        # Simple wrapper to avoid numpy dependency
        class _RNG:
            def __init__(self, seed):
                self._r = random.Random(seed)
            def choice(self, seq):
                return self._r.choice(seq)

        rng = _RNG(seed)
        wc  = self._load_wildcards()

        out_1 = self._resolve(text_1, wc, rng)
        out_2 = self._resolve(text_2, wc, rng)
        out_3 = self._resolve(text_3, wc, rng)

        return (out_1, out_2, out_3)


# ── Shared helpers ────────────────────────────────────────────────────────

COLOR_MAP = {
    "white":     (255, 255, 255),
    "black":     (0,   0,   0),
    "red":       (255, 0,   0),
    "green":     (0,   255, 0),
    "blue":      (0,   0,   255),
    "yellow":    (255, 255, 0),
    "cyan":      (0,   255, 255),
    "magenta":   (255, 0,   255),
    "orange":    (255, 165, 0),
    "purple":    (128, 0,   128),
    "pink":      (255, 192, 203),
    "brown":     (160, 85,  15),
    "gray":      (128, 128, 128),
    "lightgray": (211, 211, 211),
    "darkgray":  (102, 102, 102),
    "olive":     (128, 128, 0),
    "lime":      (0,   128, 0),
    "teal":      (0,   128, 128),
    "navy":      (0,   0,   128),
    "maroon":    (128, 0,   0),
    "fuchsia":   (255, 0,   128),
    "aqua":      (0,   255, 128),
    "silver":    (192, 192, 192),
    "gold":      (255, 215, 0),
    "turquoise": (64,  224, 208),
    "lavender":  (230, 230, 250),
    "violet":    (238, 130, 238),
    "coral":     (255, 127, 80),
    "indigo":    (75,  0,   130),
}

COLOR_LIST  = ["custom"] + sorted(COLOR_MAP.keys())
ALIGN_LIST  = ["center", "top", "bottom"]
JUSTIFY_LIST = ["center", "left", "right"]
ROTATE_LIST = ["text center", "image center"]


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _resolve_color(name, hex_fallback):
    if name == "custom":
        return _hex_to_rgb(hex_fallback)
    return COLOR_MAP.get(name, (0, 0, 0))


def _tensor2pil(t):
    arr = np.clip(255.0 * t.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _pil2tensor(img):
    return torch.from_numpy(np.array(img).astype(np.float32) / 255.0).unsqueeze(0)


def _get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _justify_x(justify, img_w, line_w, margins):
    if justify == "left":   return margins
    if justify == "right":  return img_w - line_w - margins
    return img_w / 2 - line_w / 2          # center


def _align_y(align, img_h, text_h, pos_y, margins):
    if align == "top":    return pos_y + margins
    if align == "bottom": return img_h - text_h + pos_y - margins
    return img_h / 2 - text_h / 2 + pos_y  # center


def _draw_masked_text(text_mask, text, font_path, font_size,
                      margins, line_spacing, position_x, position_y,
                      align, justify, rotation_angle, rotation_options):
    from PIL import ImageDraw, ImageFont
    draw  = ImageDraw.Draw(text_mask)
    font  = ImageFont.truetype(str(font_path), size=font_size)
    lines = text.split("\n")

    max_w = max_h = 0
    for line in lines:
        lw, lh = _get_text_size(draw, line, font)
        max_w   = max(max_w, lw)
        max_h   = max(max_h, lh + line_spacing)

    img_w, img_h   = text_mask.size
    total_text_h   = max_h * len(lines)
    text_pos_y     = position_y
    sum_plot_y     = 0
    last_plot_x    = 0

    for line in lines:
        lw, _ = _get_text_size(draw, line, font)
        plot_x = position_x + _justify_x(justify, img_w, lw, margins)
        plot_y = _align_y(align, img_h, total_text_h, text_pos_y, margins)
        draw.text((plot_x, plot_y), line, fill=255, font=font)
        last_plot_x  = plot_x
        text_pos_y  += max_h
        sum_plot_y  += plot_y

    cx = last_plot_x + max_w / 2
    cy = sum_plot_y / len(lines)

    if rotation_options == "text center":
        return text_mask.rotate(rotation_angle, center=(cx, cy))
    return text_mask.rotate(rotation_angle, center=(img_w / 2, img_h / 2))


# ── Card Titles node ───────────────────────────────────────────────────────

class CardTitles:
    """Drop-in replacement for CR Overlay Text with zero Comfyroll dependency."""

    FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

    @classmethod
    def _font_list(cls):
        if not os.path.isdir(cls.FONTS_DIR):
            return ["(no fonts found)"]
        return sorted(
            f for f in os.listdir(cls.FONTS_DIR)
            if os.path.isfile(os.path.join(cls.FONTS_DIR, f))
            and f.lower().endswith(".ttf")
        )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image":            ("IMAGE",),
                "text":             ("STRING", {"multiline": True, "default": "text"}),
                "font_name":        (cls._font_list(),),
                "font_size":        ("INT",   {"default": 50,  "min": 1,      "max": 1024}),
                "font_color":       (COLOR_LIST,),
                "align":            (ALIGN_LIST,),
                "justify":          (JUSTIFY_LIST,),
                "margins":          ("INT",   {"default": 0,   "min": -1024,  "max": 1024}),
                "line_spacing":     ("INT",   {"default": 0,   "min": -1024,  "max": 1024}),
                "position_x":       ("INT",   {"default": 0,   "min": -4096,  "max": 4096}),
                "position_y":       ("INT",   {"default": 0,   "min": -4096,  "max": 4096}),
                "rotation_angle":   ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "rotation_options": (ROTATE_LIST,),
            },
            "optional": {
                "font_color_hex": ("STRING", {"multiline": False, "default": "#000000"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION     = "overlay_text"
    CATEGORY     = "ProtoTeller"

    def overlay_text(self, image, text, font_name, font_size, font_color,
                     align, justify, margins, line_spacing,
                     position_x, position_y,
                     rotation_angle, rotation_options,
                     font_color_hex="#000000"):
        from PIL import Image as PILImage

        text_color = _resolve_color(font_color, font_color_hex)
        font_path  = os.path.join(self.FONTS_DIR, font_name)

        back_image = _tensor2pil(image[0])
        text_image = PILImage.new("RGB", back_image.size, text_color)
        text_mask  = PILImage.new("L",   back_image.size)

        rotated_mask = _draw_masked_text(
            text_mask, text, font_path, font_size,
            margins, line_spacing, position_x, position_y,
            align, justify, rotation_angle, rotation_options,
        )

        image_out = PILImage.composite(text_image, back_image, rotated_mask)
        return (_pil2tensor(image_out),)


NODE_CLASS_MAPPINGS = {
    "ConditionalImageRotate": ConditionalImageRotate,
    "ConditionalTextConcat": ConditionalTextConcat,
    "ConditionalTextSwitch": ConditionalTextSwitch,
    "DrawWildcards": DrawWildcards,
    "CardTitles": CardTitles,
    "PreviewTextImage": PreviewTextImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConditionalImageRotate": "Conditional Image Rotate",
    "ConditionalTextConcat": "Conditional Text Concat",
    "ConditionalTextSwitch": "Conditional Text Switch",
    "DrawWildcards": "Draw Wildcards",
    "CardTitles": "Card Titles",
    "PreviewTextImage": "ProtoTeller Card Reading",
}