# Mechanical Structure and 3D Models

[简体中文](README.zh-CN.md) | **English**

Mechanical files for the dual-mode ping-pong ball collector, organized into part models, print files, drawings and previews.

> Assembly relationships are documented by the multi-view photos in [`previews/`](previews/) and the assembly drawing [`solidworks/drawings/装配工程图.DWG`](<solidworks/drawings/装配工程图.DWG>). Individual dimensions are defined by the SLDPRT/STL files.

## Directory

```text
hardware/mechanical/
├── solidworks/
│   ├── parts/          13 × *.SLDPRT part models
│   └── drawings/       Assembly drawing (DWG)
├── stl/                11 × *.STL print files
├── previews/           Multi-view assembly photos + 10 part previews
└── README.md / README.zh-CN.md
```

## File Formats

| Format | Purpose | Open with |
|---|---|---|
| `.SLDPRT` | SolidWorks part source; editable dimensions/features | SolidWorks 2020 or later |
| `.DWG` | Assembly drawing (views, dimensions, tolerances) | AutoCAD / compatible CAD |
| `.STL` | Triangle mesh for slicing and printing | Cura, PrusaSlicer, Bambu Studio, JLC, etc. |
| `.png` / `.jpg` | Assembly references and part previews | Any image viewer |

## Part List

| # | Part | Preview | SLDPRT | STL | Material / process | Qty | Purpose / notes |
|---|---|---|---|---|---|---|---|
| 1 | Storage bin | [preview](previews/01-storage-box.png) | [model](<solidworks/parts/后备箱.SLDPRT>) | [STL](<stl/后备箱.STL>) | 9600 resin | 1 | Rear ball storage; side walls and ribs carry load |
| 2 | Bearing cover | [preview](previews/02-bearing-cover.png) | [model](<solidworks/parts/盒盖.SLDPRT>) | [STL](<stl/盒盖.STL>) | PA12 | 1 | Locates the free-end bearing; installed |
| 3 | Three-blade rotor | [preview](previews/03-blade.png) | [model](<solidworks/parts/叶片.SLDPRT>) | [STL](<stl/叶片.STL>) | PA12 | 1 set | Rotates and pushes balls |
| 4 | Blade shaft (roller coupling) | [preview](previews/04-blade-shaft.png) | [model](<solidworks/parts/叶片轴（滚轴交接）.SLDPRT>) | [STL](<stl/叶片轴（滚轴交接）.STL>) | BJ-316L stainless steel | 1 | Axial coupling of rotor and adjacent parts |
| 5 | Left guide claw | [preview](previews/05-guide-claws.png) | [model](<solidworks/parts/左爪.SLDPRT>) | [STL](<stl/左爪.STL>) | 3201PA-F | 1 | Left curved guide, widens inlet |
| 6 | Right guide claw | [preview](previews/05-guide-claws.png) | [model](<solidworks/parts/右爪.SLDPRT>) | [STL](<stl/右爪.STL>) | 3201PA-F | 1 | Right curved guide |
| 7 | Front top baffle | [preview](previews/06-front-top-baffle.png) | [model](<solidworks/parts/前挡顶.SLDPRT>) | [STL](<stl/前挡顶.STL>) | 3D printed (material TBD) | 1 | Front cross member / alignment |
| 8 | Single bracket | [preview](previews/07-single-bracket.png) | [model](<solidworks/parts/单支架.SLDPRT>) | [STL](<stl/单支架.STL>) | PA12 | 2 | Raises and adjusts the rear bin |
| 9 | Double bracket | [preview](previews/08-double-bracket.png) | [model](<solidworks/parts/双支架.SLDPRT>) | [STL](<stl/双支架.STL>) | PA12 | 1 set | Dual-side support |
| 10 | Reinforced arch top | [preview](previews/09-arch-top.png) | [model](<solidworks/parts/拱顶（强化）.SLDPRT>) | [STL](<stl/拱顶(强化）.STL>) | 9600 resin | 2 | Cross beam; mounts adjustable brackets and DCDC |
| 11 | Front collector body | [preview](previews/assembly-front.jpg) | [model](<solidworks/parts/车前端.SLDPRT>) | [STL](<stl/车前端.STL>) | 3201PA-F | 1 | Main front collection body |
| 12 | 605.ZZ bearing | [preview](previews/10-bearing-605zz.png) | — | — | Purchased (5 × 11 × 5 mm) | 1 | Low-friction free-end support |

Auxiliary model: `电池.SLDPRT` (battery pack placeholder). Assembly drawing: [`solidworks/drawings/装配工程图.DWG`](<solidworks/drawings/装配工程图.DWG>).

> `拱顶(强化）.STL` uses a half-width left parenthesis and a full-width right parenthesis; copy the filename exactly.

## Assembly References

See [`previews/README.md`](previews/README.md) for full-car photos and part previews.

| Front collection mechanism | Full car, side view |
|---|---|
| ![Front](previews/assembly-front.jpg) | ![Side](previews/assembly-side2.jpg) |

During assembly, check: left/right claw orientation, blade-to-channel clearance, bearing/cover/shaft concentricity, and alignment between the rear bin inlet and the front channel.

## Materials and Quantities

| Material | Parts | Notes |
|---|---|---|
| 9600 resin | Storage bin, reinforced arch top | Matte white; bin sanded/rough-finished |
| 3201PA-F | Left/right claws, front collector body | Grey-black; tough and impact-resistant |
| PA12 | Rotor, bearing cover, single/double brackets | Grey-black; rotor is a loaded rotating part |
| BJ-316L stainless steel | Blade shaft | Wear and corrosion resistant |
| Purchased | 605.ZZ bearing, M3 fasteners | One deep-groove bearing |

3D printing totals about CNY 416.44 (JLC quote; varies with volume/material/lead time): front body 120.64, bin 127.01, rotor 70.60, left claw 55.17, arch top 2×6.32, bearing cover 5.15, double bracket 5.49, single bracket 2×4.87, blade shaft 10.00.

## Fasteners

M3 standard hardware, assembly quantities:

| Size | Qty |
|---|---:|
| M3×7 | 8 |
| M3×8 | 4 |
| M3×9 | 8 |
| M3×10 | 6 |
| M3×12 | 6 |
| M3×25 | 2 |
| M3×30 | 2 |
| **Screws total** | **36** |
| M3 nuts | 36 |

Buy in full packs (100/200 pcs); unit prices are in the main README cost table.

## Printing and Assembly Notes

1. **Units and orientation**: STLs are in millimetres. Check the bounding box and orientation before slicing; for large parts (bin, front body), prioritize a flat base and removable supports.
2. **Warping**: printed parts warp; check flatness before assembly and leave sanding allowance on the bin/front body.
3. **Concentricity**: the rotor is motor-driven at one end and bearing-supported at the other. Turn it by hand after assembly; recheck bearing, cover and roller-coupling alignment.
4. **Clearance**: leave enough clearance between the rotor, channel and bin inlet; no collision in CAD does not guarantee no collision in reality—verify on the car.
5. **Ball path**: claws → rotor → bin inlet should form a smooth path. A bent wire stop can be added to the guide-claw gaps to reduce jams.
6. **Fastening**: use M3 screws with nuts and washers on loaded joints. Tap printed holes or use self-tapping screws to avoid cracking.

## Drawing

- `装配工程图.DWG`: side, front, top and isometric views for checking the overall envelope and module positions.
- The drawing remains the primary assembly/manufacturing reference. Local dimensions, bin mounting holes and shaft/bearing tolerances still need to be completed.

## License

The original parts, drawings and preview images in this directory were created by the project team and are released under the **MIT License**.
