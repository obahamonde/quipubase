import path from "node:path";
import { defineConfig } from "vite";
import Vue from "@vitejs/plugin-vue";
import Pages from "vite-plugin-pages";
import Layouts from "vite-plugin-vue-layouts"; // eslint-disable-line
import Components from "unplugin-vue-components/vite";
import AutoImport from "unplugin-auto-import/vite";
import Markdown from "vite-plugin-vue-markdown";
import VueDevTools from "vite-plugin-vue-devtools";
import LinkAttributes from "markdown-it-link-attributes";
import Unocss from "unocss/vite";
import Shiki from "markdown-it-shiki";
import VueMacros from "unplugin-vue-macros/vite";

export default defineConfig({
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "~/styles/variables.scss";`,
      },
    },
  },
  resolve: {
    alias: {
      "~/": `${path.resolve(__dirname, "src")}/`,
    },
  },
  server: {
    proxy: {
      "/api": {
        target: "https://6bxwkv84qjspb1-8000.proxy.runpod.net/api",
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api/, ""),
      },
    },
    watch: {
      usePolling: true,
      ignored: ["**/node_modules/**", "**/dist/**", "**/.git/**", "**/api/**"],
    },
  },
  build: {
    outDir: "static",
    emptyOutDir: true,
  },
  plugins: [
    VueMacros({
      plugins: {
        vue: Vue({
          include: [/\.vue$/, /\.md$/],
        }),
      },
    }),
    Pages({
      extensions: ["vue", "md"],
    }),
    Layouts(),
    AutoImport({
      imports: ["vue", "vue-router", "@vueuse/head", "@vueuse/core"],
      dts: "src/auto-imports.d.ts",
      dirs: ["src/composables", "src/stores", "src/types"],
      vueTemplate: true,
    }),
    Components({
      extensions: ["vue", "md"],
      include: [/\.vue$/, /\.vue\?vue/, /\.md$/],
      dts: "src/components.d.ts",
    }),
    Unocss(),
    Markdown({
      wrapperClasses: "prose prose-sm m-auto text-left",
      headEnabled: true,
      markdownItSetup(md) {
        md.use(Shiki, {
          theme: {
            light: "vitesse-light",
            dark: "vitesse-dark",
          },
        });
        md.use(LinkAttributes, {
          matcher: (link: string) => /^https?:\/\//.test(link),
          attrs: {
            target: "_blank",
            rel: "noopener",
          },
        });
      },
    }),
    VueDevTools(),
  ],
});
