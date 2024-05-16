import { setupLayouts } from "virtual:generated-layouts";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import { createApp } from "vue";
import { Icon } from "@iconify/vue";
import App from "./App.vue";
import generatedRoutes from "~pages";
import piniaPluginPersistedstate from "pinia-plugin-persistedstate";
import { createAuth0 } from "@auth0/auth0-vue";

import "./styles/main.scss";
import "uno.css";

const routes = setupLayouts(generatedRoutes);
const router = createRouter({
  history: createWebHistory(),
  routes,
});
const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
createApp(App)
  .use(pinia)
  .component("Icon", Icon)
  .use(
    createAuth0({
      domain: "dev-tvhqmk7a.us.auth0.com",
      clientId: "53p0EBRRWxSYA3mSywbxhEeIlIexYWbs",
      authorizationParams: {
        redirect_uri: window.location.origin,
      },
    }),
  )
  .use(router)
  .mount("#app");
