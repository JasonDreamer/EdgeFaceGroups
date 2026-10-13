# Edge/Face Groups

A Blender add-on that gives edge and face attributes a panel that works like Vertex Groups.

Each group is a `FLOAT` mesh attribute on the `EDGE` or `FACE` domain, so Geometry Nodes and other tools can read it by name.

## Requirements

Blender 5.1.1 or later.

## Install

1. Download `edge_face_groups-v0.1.0.zip` from the [Releases](../../releases) page.
2. In Blender, open **Edit > Preferences > Add-ons**, choose **Install from Disk**, and select the zip.
3. Enable **Edge/Face Groups**.

## Usage

The **Edge Groups** and **Face Groups** panels appear in **Properties > Data** for mesh objects.

- **+ / -** adds or removes a group.
- In Edit Mode:
  - **Weight** sets the value written by Assign (0 to 1).
  - **Assign** writes the weight to the selected edges or faces.
  - **Remove** sets the selected elements back to 0.
  - **Select / Deselect** changes the selection of elements whose value is above 0.

New groups are named `edge_group` and `face_group` by default. The prefixes can be changed in the add-on preferences.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
