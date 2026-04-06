import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "ProtoTeller.PreviewTextImage",

    async nodeCreated(node) {
        if (node.comfyClass !== "PreviewTextImage") return;

        // ── Kill ComfyUI's built-in image renderer entirely ────────────
        node.onDrawBackground = function () {};
        node.imgs = null;

        // Intercept ComfyUI trying to set imgs after execution
        Object.defineProperty(node, "imgs", {
            get() { return null; },
            set(_v) {},
            configurable: true,
        });

        // ── Hide the native STRING text widget ─────────────────────────
        const hideNativeTextWidget = () => {
            const textWidget = node.widgets?.find(w => w.name === "text");
            if (textWidget) {
                textWidget.type = "hidden";
                textWidget.computeSize = () => [0, -4];
            }
        };
        hideNativeTextWidget();
        setTimeout(hideNativeTextWidget, 0);

        // ── Panel container ────────────────────────────────────────────
        const panel = document.createElement("div");
        panel.style.cssText = `
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            padding: 8px;
            width: 100%;
            box-sizing: border-box;
        `;

        // ── Image preview ──────────────────────────────────────────────
        const imgEl = document.createElement("img");
        imgEl.style.cssText = `
            width: 100%;
            border-radius: 4px;
            display: none;
            object-fit: contain;
        `;
        panel.appendChild(imgEl);

        // ── Text preview ───────────────────────────────────────────────
        const textEl = document.createElement("div");
        textEl.style.cssText = `
            width: 100%;
            min-height: 120px;
            max-height: 600px;
            overflow-y: auto;
            padding: 10px;
            background: #2a2a2a;
            border-radius: 4px;
            color: #ddd;
            font-size: 12px;
            font-family: monospace;
            white-space: pre-wrap;
            word-break: break-word;
            box-sizing: border-box;
            display: none;
            line-height: 1.5;
        `;
        panel.appendChild(textEl);

        // ── Attach DOM widget ──────────────────────────────────────────
        node.addDOMWidget("preview_panel", "preview", panel, {
            getValue() { return null; },
            setValue() {},
            computeSize() {
                return [node.size[0], 1100];
            },
        });

        // ── Update panel on execution ──────────────────────────────────
        const onExecuted = node.onExecuted?.bind(node);
        node.onExecuted = function (output) {
            onExecuted?.(output);
            node.outputs_ui = output;

            if (output?.images?.[0]) {
                const img = output.images[0];
                const subfolder = img.subfolder
                    ? `&subfolder=${encodeURIComponent(img.subfolder)}`
                    : "";
                imgEl.src = `/view?filename=${encodeURIComponent(img.filename)}${subfolder}&type=${img.type}&t=${Date.now()}`;
                imgEl.style.display = "block";
            }

            if (output?.text?.[0] !== undefined) {
                textEl.textContent = output.text[0];
                textEl.style.display = "block";
            }
        };
    },
});