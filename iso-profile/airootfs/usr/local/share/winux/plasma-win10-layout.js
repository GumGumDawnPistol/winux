// WINUX Windows 10-style KDE Plasma 6 layout script
// Applied once on first login via winux-apply-theme (or anytime with --force).

var existingPanels = panels();
for (var i = 0; i < existingPanels.length; i++) {
    existingPanels[i].remove();
}

var taskbar = new Panel("org.kde.panel");
taskbar.location = "bottom";
taskbar.height = 44;
taskbar.hiding = "none";

// Windows 10 Start Menu
var kickoff = taskbar.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["General"];
kickoff.writeConfig("icon", "/usr/share/icons/winux/winux-start.svg");
kickoff.writeConfig("favoritesPortedToKAstats", "true");
kickoff.currentConfigGroup = ["Shortcuts"];
kickoff.writeConfig("global", "Alt+F1");

// Pinned Windows-style Icons-Only Task Manager
var tasks = taskbar.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:firefox.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:winux-manager.desktop",
    "applications:steam.desktop"
].join(","));
tasks.writeConfig("groupingStrategy", "1");
tasks.writeConfig("middleClickAction", "2");

// System Tray, Clock, and Far-Right Show Desktop Peek
taskbar.addWidget("org.kde.plasma.marginsseparator");
taskbar.addWidget("org.kde.plasma.systemtray");

var clock = taskbar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("use24hFormat", "0");

taskbar.addWidget("org.kde.plasma.showdesktop");

// Apply WINUX hero wallpaper across all desktops
var allDesktops = desktops();
for (var d = 0; d < allDesktops.length; d++) {
    var desk = allDesktops[d];
    desk.wallpaperPlugin = "org.kde.image";
    desk.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desk.writeConfig("Image", "file:///usr/share/wallpapers/winux/winux-hero.svg");
}
