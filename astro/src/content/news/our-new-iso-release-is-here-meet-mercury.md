---
title: "Our new ISO release is here, meet Mercury"
description: "Mercury arrives with Linux 6.13.1, a memory test in the EFI boot menu, dark themes by default on the larger desktops, and a fix for BIOS and legacy installs."
date: 2025-02-10
author: "Bryanpwo"
hero: "../../assets/news/2025/EndeavourOS_Mercury_livesession.png"
heroAlt: "The EndeavourOS Mercury live session: the Calamares installer's welcome screen open over the Mercury wallpaper, with the desktop taskbar along the bottom."
heroDecorative: false
---

It has been a while since we released our last ISO, Endeavour Neo, and even though this new ISO comes with many improvements and technical challenges we had to tackle, like resolving issues that came with Linux kernel 6.13, the Xfce 4.20 update, sfdisk and Calamares’ kpmcore, those challenges weren’t the main reason for the long hiatus between Endeavour Neo and Mercury.

No, it simply was that well-known song of life getting in the way and this situation won’t change for some time. Let me reassure you that we are not planning to throw in the towel, but you will have to get used to a somewhat irregular release schedule from us for now. This doesn’t mean that our ISOs will be left to deteriorate during availability. **Every ISO receives and has received hotfixes during their run which will be fetched automatically before the installer starts doing its magic.** The only major issue that can happen with this method is that the newest hardware possibly won’t boot our ISO due to an older kernel version over time. We will resolve those as soon as we can with Neo and Nova releases.

One of the main reasons for our irregular release schedule is that Joe Kamprad is busy studying to be a certified programmer and I’m sure you can understand this is taking a lot of time and energy, but in the end, it will benefit the project. So, we’re still alive and kicking!

Before I go on into the release notes of our Mercury release I’d like to highlight the following:

**The changes described over here are affecting new installs, our Calamares installer, and the Live environment on the ISO only. Running systems don’t have to “upgrade” to Mercury, if you update regularly your system is fine.**

## The Mercury release

![](../../assets/news/2025/Mercury.jpeg)

Image by Unclespellbinder

The Mercury ISO ships with the following packages for both the live environment and the offline install option:

**Calamares 25.02.1.4-3 
Firefox 135.0-1 
Linux 6.13.1.arch2-1 
Mesa 1:24.3.4-1 
Xorg-server 21.1.15-1 (xorg) 
Nvidia 570.86.16-3**

## New Features and improvements:

- The ISO now has a memory test for EFI too.

- The issue with Bios/Legacy Installs is resolved.

- KDE, Gnome, XFCE4, Mate, Budgie and Cinnamon use a dark theme by default.

- XFCE4 theme is now closer to the default (Xfce) setup.

- Gnome sets dark and light wallpapers on changing mode automatically

- Replacing empty space with the “replace Partition” option is working again.

- The installer showing double entries for the EFI selection dropdown is resolved.

- EndeavourOS Branding is easier to find and use for artists and media usage. → [https://github.com/endeavouros-team/Branding](https://github.com/endeavouros-team/Branding)

- Both mirrorlists ranked now before installation will be copied to the target. In case the user changes the mirror list on the live session, these will be used instead, and not ranked in the installation process again.

You can download the ISO over [here](/download/).
