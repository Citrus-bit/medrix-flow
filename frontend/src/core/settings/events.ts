export const OPEN_SETTINGS_EVENT = "medrix:open-settings";

export type OpenSettingsDetail = {
  section?:
    | "setup"
    | "appearance"
    | "memory"
    | "tools"
    | "skills"
    | "notification"
    | "about";
};

export function dispatchOpenSettings(
  detail: OpenSettingsDetail = { section: "setup" },
) {
  window.dispatchEvent(
    new CustomEvent<OpenSettingsDetail>(OPEN_SETTINGS_EVENT, { detail }),
  );
}
