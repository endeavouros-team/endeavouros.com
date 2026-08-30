---
title: "Ganymede Neo is out with core updates and upstream NVIDIA changes"
description: "We’re kicking off 2026 with the release of Ganymede Neo. As you are accustomed to with our Neo releases, this release includes upstream updates and minor..."
date: 2026-01-15
author: "Bryanpwo"
hero: "../../assets/news/2025/EndeavourOS_Ganymede__3840x2160-scaled.jpg"
heroAlt: ""
heroDecorative: true
---

We’re kicking off 2026 with the release of Ganymede Neo. As you are accustomed to with our Neo releases, this release includes upstream updates and minor changes compared to the [Ganymede ISO](/news/the-long-wait-is-over-ganymede-has-arrived/).

Before I go into the release notes, I just want to remind you of the following.

**The changes described over here are affecting new installs, our Calamares installer, and the Live environment on the ISO only. Running systems don’t have to “upgrade” to Ganymede Neo; if you update regularly, your system is fine.**

## The Ganymede Neo release

This ISO and offline installer ships with:

**Calamares 26.01.1.5-1 
Firefox 146.0.1-1 
Linux 6.18.4.arch1-1 
Mesa 1:25.3.3-2 
Xorg-server 21.1.21-1 (xorg) 
Nvidia-utils 590.48.01-2**

And has the following bugfixes:

- The long startup time issue with** Calamares** has been resolved.

- The package **Nemo preview** was removed from the default package bundle for **Cinnamon** and **Budgie** during installation due to its removal from the Arch repository.

- Starting with this release, the **NVIDIA proprietary drivers** have been switched to nvidia-open due to the upstream changes to NVIDIA drivers: [https://archlinux.org/news](https://archlinux.org/news/nvidia-590-driver-drops-pascal-support-main-packages-switch-to-open-kernel-modules). As a result, the proprietary option now only supports Turing GPUs(16xx) and later. Earlier NVIDIA GPUs are still supported using the default boot option, which will use the Nouveau open-source drivers.

These are all the changes Ganymede Neo ships with to ensure a smooth ISO boot and installation. We are currently hard at work with further refinements and additions for Ganymede’s successor,** *Titan****.* So keep an eye out for our announcements.

Ganymede Neo is available on [our homepage](/).
