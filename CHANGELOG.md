# Changelog
All notable pypsbuilder changes.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 2021-XX-YY
### Fixed
- latest THERMOCALC 3.50 compatibility

## [2.2.2] - 2021-01-25
### Fixed
- gendrawpd fixed
- fix to partially support TC347

## [2.2.1] - 2020-06-16
### Added
- bugfix release
- option to to move invpoint and keep results
(useful to fine-tune topology)
- tool to cleanup storage (trim metastable calculations)
- option to hide labels of connected lines and points

## [2.2.0] - 2020-04-11
### Added
- ptbuilder, txbuilder and pxbuilder pseudosection builders
- topology graph window added
- dogmin implemented (results stored in projects)
- autoconnect implemented
- invariant point search implemented
- merge of partially calculated univariant lines implemented
- possibility to remove parts of univariant lines implemented
- zoom to uni added to context menu
- option to extend calculation range to extend univariant lines gently out of defined region
- PTPS, TXPS and PXPS psexplorers implemented
- possibility to merge several parts of pseudosection. Invariant points and
univariant lines must be unique in single project.
- calc along PT path implemented (now only for PT sections)

## [2.1.5] - 2019-03-25
### Removed
- autocorrection of liquid model named as liq but starting guesses using L removed.
User must check if liq model is coded properly. In case of tc-6xmn.txt it should be:

```
  % =================================================
  liq 8  1

     q(liq)          0.1814
     fsp(liq)        0.3490
     na(liq)         0.5840
     an(liq)        0.01104
     ol(liq)        0.01373
     x(liq)          0.7333
     h2o(liq)        0.4276

  % --------------------------------------------------
```

## [2.1.4] - 2017-12-04
### Fixed
- clabel positioning
- minimum contour level
- silently ignore critical possible topology errors

## [2.1.2] - 2017-04-03
### Added
- Option to show bulk composition on psexplorer figures
- dio-o and gl-act-hb added to polymorphs

### Fixed
- psshow changed default color map to be darker for higher variance
- manual or imported invariant points bub in psiso fixed

## [2.1.1] - 2017-03-28
### Added
- colors and cmap args added to cli version of psiso
- clabel arg psiso to place contour labels

## [2.1.0] - 2017-03-23
### Added
- Write starting guesses from existing calculations
(note that commented tags are needed in scriptfile)
- Updated parsing include rbi data
- Initial version of psexplorer to draw final pseudosections and isopleths
(cli scrips provided)
- Manual unilines and invpoints shown in bold in lists

## [2.0.7] - 2017-02-13
### Added
- double-click on phaselist highlight all unilines with zero mode phase
- option to export partial areas
- Keyboard shortcuts added Ctrl-T and Ctrl-P for CalcTatP and CalcPatT,
Ctrl-H Zoom home

### Fixes
- excess phases stored in unilines and invpoints
- labeling phases sorted alphabeltically, same as phaselist
- auto bug fixed

## [2.0.6] - 2017-02-03
### Fixed
- path to executables stored in project
- scriptfile parsing improved

## [2.0.5] 2017-01-19
### Fixes
- output parsing fixed (hopefully...)
- Rightclick invariant points menu fixed
- area construction for drawpd export fixed
- networkx dependecy removed

## [2.0.4] - 2017-01-13
### Added
- saveas project added
- working directory written to Log window
- Log window catch output of both thermocalc and drawpd

## [2.0.3] - 2017-01-13
### Added
- invview right click to select not yet calculated uni lines implemented

### Fixes
- Zoom uni button persistent
- export list of phases in areas for TC-Investigator
- drawpd areas construction fixed

## [2.0.2] - 2016-12-10
### Fixed
- Areas export fixed
- inv filtering fixed

## [2.0.1] - 2016-12-10
### Added
- Recent files implemented
- Adding manual uni and inv must be constrained by phases and out selection
- Export areas to drawpd
- Auto calculation around inv point

### Fixed
- scriptfile encoding fix
- unilabels placement fixed
- refresh instead plot during zoom
- new unicutting algorithm
- THERMOCALC mac-roman encoding used

## [2.0.0] 2016-11-19
### Added
- Initial release of new generation of PSBuilder

[Unreleased]: https://github.com/ondrolexa/pypsbuilder/compare/v2.2.2...HEAD
[2.2.2]: https://github.com/ondrolexa/pypsbuilder/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/ondrolexa/pypsbuilder/compare/v2.1.5...v2.2.1