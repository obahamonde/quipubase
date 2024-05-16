import {
  defineConfig,
  presetAttributify,
  presetIcons,
  presetTypography,
  presetUno,
  presetWebFonts,
  transformerDirectives,
  transformerVariantGroup,
} from "unocss";

export default defineConfig({
  shortcuts: [
    ["scale", "hover:scale-110 hover:transition-all duration-200 ease-in-out"],
    ["cp", "cursor-pointer"],
    ["rf", "rounded-full"],
    ["col", "flex flex-col"],
    ["row", "flex flex-row"],
    ["center", "items-center justify-center"],
    ["start", "items-start justify-start"],
    ["end", "items-end justify-end"],
    ["tr", "top-0 right-0"],
    ["br", "bottom-0 right-0"],
    ["bl", "bottom-0 left-0"],
    ["tl", "top-0 left-0"],
    ["sh", "shadow-gray-500 shadow-md"],
    ["sh-sm", "shadow-sm"],
    ["sh-md", "shadow-md"],
    ["sh-lg", "shadow-lg"],
    ["sh-xl", "shadow-xl"],
    ["sh-2xl", "shadow-2xl"],
    ["scale", "hover:scale-110 hover:transition-all duration-200 ease-in-out"],
    ["grid2", "grid grid-cols-2"],
    ["grid3", "grid grid-cols-3"],
    ["grid4", "grid grid-cols-4"],
    ["grid5", "grid grid-cols-5"],
    ["grid6", "grid grid-cols-6"],
    ["slide-up", "animate-slide-in-up animate-duration-200"],
    ["slide-down", "animate-slide-in-down animate-duration-200"],
    ["slide-left", "animate-slide-in-left animate-duration-200"],
    ["slide-right", "animate-slide-in-right animate-duration-200"],
    ["fade-in", "animate-fade-in animate-duration-200"],
    ["fade-in-up", "animate-fade-in-up animate-duration-200"],
    ["fade-in-down", "animate-fade-in-down animate-duration-200"],
    ["fade-in-left", "animate-fade-in-left animate-duration-200"],
    ["fade-in-right", "animate-fade-in-right animate-duration-200"],
    ["spin-in-up", "animate-spin-in-up animate-duration-200"],
    ["spin-in-down", "animate-spin-in-down animate-duration-200"],
    ["spin-in-left", "animate-spin-in-left animate-duration-200"],
    ["spin-in-right", "animate-spin-in-right animate-duration-200"],
    ["no-outline", "outline-none focus:outline-none hover:outline-none"],
    [
      "btn-get",
      "dark:invert m-2 bg-primary text-light rounded-lg shadow-success hover:bg-success hover:text-accent hover:shadow-primary shadow-md px-4 py-2 cp hover:scale-110 hover:transition-all duration-200 ease-in-out hover:cursor-pointer hover:font-extrabold hover:underline",
    ],
    [
      "btn-del",
      "dark:invert m-2 bg-error text-light rounded-lg shadow-warning hover:bg-warning hover:text-error hover:shadow-error shadow-md px-4 py-2 cp hover:scale-110 hover:transition-all duration-200 ease-in-out hover:cursor-pointer hover:font-extrabold hover:underline",
    ],
    [
      "btn-post",
      "dark:invert m-2 bg-success text-accent rounded-lg shadow-primary hover:bg-primary hover:text-light hover:shadow-success shadow-md px-4 py-2 cp hover:scale-110 hover:transition-all duration-200 ease-in-out hover:cursor-pointer hover:font-extrabold hover:underline",
    ],
    [
      "btn-put",
      "dark:invert m-2 bg-warning text-light rounded-lg shadow-info hover:bg-info hover:text-light hover:shadow-warning shadow-md px-4 py-2 cp hover:scale-110 hover:transition-all duration-200 ease-in-out hover:cursor-pointer hover:font-extrabold hover:underline",
    ],
    [
      "text-caption",
      "font-mono text-success dark:text-light text-sm text-center",
    ],
    [
      "text-title",
      "font-script text-accent dark:text-secondary text-xl text-center",
    ],
    ["text-body", "font-serif text-black dark:text-light text-lg"],
    [
      "text-subtitle",
      "font-sans text-primary dark:text-success text-lg text-center",
    ],
    [
      "input",
      "my-2 p-1 rounded-lg shadow-primary sh-md border text-info dark:text-light border-primary dark:border-light dark:bg-dark dark:text-light outline-none",
    ],
    ["btn-icon", "p-1 scale cp x2 m-1 rounded-full"],
    ["over", "shadow-gray-500 shadow-lg"],
    [
      "container",
      "text-center mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-16 xl:py-20 2xl:py-24",
    ],
    [
      "footer-link",
      "text-4xl text-black opacity-100 transition-all duration-500 ease-in-out bg-transparent hover:scale-150 hover:mr-4 hover:text-white hover:opacity-100 hover:shadow-xl hover:bg-transparent hover:translate--y-4 hover:translate-x-4",
    ],
    [
      "footer-container",
      "flex flex-row items-center justify-center bottom-0 right-0 left-0 fixed z-50 mx-auto h-16 gap-4 w-1/2 opacity-50 hover:opacity-100 transition-all duration-500 ease-in-out bg-gray-500 rounded-lg shadow-lg cursor-pointer hover:shadow-xl hover:bg-gray-600 hover:text-white hover:opacity-100 text-black text-3xl rounded-full",
    ],
    [
      "card-title",
      "mb-3 text-2xl text-title text-black dark:text-white font-semibold",
    ],
  ],
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      warn: true,
    }),
    presetTypography(),
    presetWebFonts({
      fonts: {
        sans: "Inter",
        serif: "Alegreya",
        mono: "DM Mono",
        script: "Merienda",
      },
    }),
  ],
  transformers: [transformerDirectives(), transformerVariantGroup()],
  safelist: "prose prose-sm m-auto text-left".split(" "),
  theme: {
    colors: {
      primary: "#2A5EC0",
      secondary: "#16EED1",
      accent: "#000080",
      warning: "#fe8a71",
      error: "#ee5253",
      info: "#fefefe",
      success: "#c4e538",
    },
  },
  rules: [
    [
      /^x(\d+)$/,
      ([, d]) => ({
        height: `${d}rem`,
        width: `${d}rem`,
      }),
    ],
    [
      /^[bg|border|color|fill|outline|shadow|text]-(.*)$/,
      ([, attr, color], { theme }) => {
        if (color in theme.colors) {
          switch (attr) {
            case "bg":
              return {
                backgroundColor: theme.colors[color],
              };
            case "border":
              return {
                borderColor: theme.colors[color],
              };
            case "color":
              return {
                color: theme.colors[color],
              };
            case "fill":
              return {
                fill: theme.colors[color],
              };
            case "outline":
              return {
                outlineColor: theme.colors[color],
              };
            case "shadow":
              return {
                shadowColor: theme.colors[color],
              };
            case "text":
              return {
                color: theme.colors[color],
              };
          }
        }
      },
    ],
  ],
});
