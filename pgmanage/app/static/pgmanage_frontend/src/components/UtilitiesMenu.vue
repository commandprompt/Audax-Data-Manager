<template>
  <div
    class="omnidb__utilities-menu omnidb__theme-bg--menu-utilities omnidb__rounded--lg"
    :class="{ 'omnidb__utilities-menu--show': menuExpanded }"
  >
    <nav class="navbar p-0">
      <span class="omnidb__utilities-menu__branding"></span>
      <div id="navbarSecond">
        <div class="navbar-nav flex-row">
          <a
            id="omnidb__utilities-menu__link-versioning"
            class="omnidb__menu__btn-text-visible nav-item nav-link d-flex align-items-center justify-content-center"
          >
            <i class="fas fa-code-branch"></i>
            <span class="badge badge-info">{{ shortVersion }}</span>
          </a>
          <a
            v-if="!desktopMode"
            id="omnidb__utilities-menu__link-username"
            class="omnidb__menu__btn-user omnidb__menu__btn-text nav-item nav-link d-flex align-items-center justify-content-center"
          >
            <span>{{ userName }}</span>
          </a>
          <template v-for="menuItem in extraItems">
            <a
              v-if="menuItem.show"
              :id="menuItem.id"
              class="omnidb__menu__btn nav-item nav-link"
              @click="menuItem.clickFunction"
              href="#"
            >
              <i :class="menuItem.icon" :title="menuItem.name"></i>
            </a>
          </template>
          <a
            id="omnidb__utilities-menu__link-config"
            class="omnidb__menu__btn nav-item nav-link"
            href="#"
            @click="showSettings"
            ><i class="fas fa-cog" title="Settings"></i
          ></a>
          <a
            id="omnidb__utilities-menu__link-about"
            data-bs-toggle="modal" data-bs-target="#modal_about"
            class="omnidb__menu__btn nav-item nav-link"
            href="#"
            ><i class="fas fa-info-circle" title="About"></i
          ></a>
          <a
            v-if="!desktopMode"
            id="omnidb__utilities-menu__link-signout"
            class="omnidb__menu__btn nav-item nav-link"
            href="#"
            @click="confirmSignout"
            ><i class="fas fa-sign-out-alt" title="Sign out"></i
          ></a>
          <a
            ref="toggleButton"
            id="omnidb__utilities-menu__link-toggle"
            class="omnidb__menu__btn nav-item nav-link"
            href="#"
            @click="toggleUtilitiesMenu"
            ><i class="fas fa-tools" title="Utilities Menu"></i
          ></a>
        </div>
      </div>
    </nav>
  </div>
</template>

<script>
import {
  messageModalStore,
  settingsStore,
  utilitiesMenuStore,
} from "../stores/stores_initializer.js";

export default {
  name: "UtilitiesMenu",
  data() {
    return {
      shortVersion: window.short_version,
      userName: window.user_name,
      menuExpanded: false,
    };
  },
  computed: {
    desktopMode() {
      return settingsStore.desktopMode;
    },
    extraItems() {
      return utilitiesMenuStore.items;
    },
  },
  watch: {
    menuExpanded(newVal) {
      if (newVal) {
        document.addEventListener("click", this.handleOutsideClick);
      } else {
        document.removeEventListener("click", this.handleOutsideClick);
      }
    },
  },
  methods: {
    toggleUtilitiesMenu() {
      this.menuExpanded = !this.menuExpanded;
    },
    showSettings() {
      settingsStore.showModal();
    },
    confirmSignout() {
      messageModalStore.showModal("Are you sure you want to sign out?", () => {
        window.open("../logout", "_self");
      });
    },
    handleOutsideClick(e) {
      if (
        !(
          this.$refs.toggleButton === e.target ||
          this.$refs.toggleButton.contains(e.target)
        )
      ) {
        this.menuExpanded = false;
      }
    },
  },
};
</script>
