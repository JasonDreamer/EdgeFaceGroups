# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Edge/Face Groups",
    "author": "",
    "version": (0, 1, 0),
    "blender": (5, 1, 1),
    "location": "Properties > Data",
    "description": "Vertex Groups-like UI for Edge/Face attribute groups",
    "category": "Mesh",
}

import bpy
import bmesh


def _get_prefs():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def _get_prefixes():
    prefs = _get_prefs()
    if prefs:
        return prefs.edge_prefix, prefs.face_prefix
    return "edge_group", "face_group"


def _unique_name(base, existing_names):
    if base not in existing_names:
        return base
    idx = 1
    while True:
        name = f"{base}.{idx:03d}"
        if name not in existing_names:
            return name
        idx += 1


def _is_edge_group(attr):
    try:
        return attr.domain == 'EDGE' and attr.data_type == 'FLOAT'
    except ReferenceError:
        return False
    except AttributeError:
        return False


def _is_face_group(attr):
    try:
        return attr.domain == 'FACE' and attr.data_type == 'FLOAT'
    except ReferenceError:
        return False
    except AttributeError:
        return False


def _get_active_attr(mesh, domain, allow_write=False):
    if domain == 'EDGE':
        name = mesh.edge_group_active_name
        index = mesh.edge_group_index
    else:
        name = mesh.face_group_active_name
        index = mesh.face_group_index
    if name:
        attr = mesh.attributes.get(name)
        if attr and attr.domain == domain:
            return attr
    if 0 <= index < len(mesh.attributes):
        attr = mesh.attributes[index]
        if _is_edge_group(attr) if domain == 'EDGE' else _is_face_group(attr):
            if allow_write:
                if domain == 'EDGE':
                    mesh.edge_group_active_name = attr.name
                else:
                    mesh.face_group_active_name = attr.name
            return attr
    return None


def _ensure_active_name(mesh, domain, allow_write=False):
    attrs = [a for a in mesh.attributes if (
        _is_edge_group(a) if domain == 'EDGE' else _is_face_group(a)
    )]
    if domain == 'EDGE':
        if mesh.edge_group_active_name and mesh.edge_group_active_name in mesh.attributes:
            return
        if attrs:
            if allow_write:
                mesh.edge_group_active_name = attrs[0].name
                mesh.edge_group_index = mesh.attributes.find(attrs[0].name)
        else:
            if allow_write:
                mesh.edge_group_active_name = ""
                mesh.edge_group_index = -1
    else:
        if mesh.face_group_active_name and mesh.face_group_active_name in mesh.attributes:
            return
        if attrs:
            if allow_write:
                mesh.face_group_active_name = attrs[0].name
                mesh.face_group_index = mesh.attributes.find(attrs[0].name)
        else:
            if allow_write:
                mesh.face_group_active_name = ""
                mesh.face_group_index = -1


def _update_active_edge_index(self, _context):
    if 0 <= self.edge_group_index < len(self.attributes):
        attr = self.attributes[self.edge_group_index]
        if _is_edge_group(attr):
            self.edge_group_active_name = attr.name
            return
    _ensure_active_name(self, 'EDGE', allow_write=True)


def _update_active_face_index(self, _context):
    if 0 <= self.face_group_index < len(self.attributes):
        attr = self.attributes[self.face_group_index]
        if _is_face_group(attr):
            self.face_group_active_name = attr.name
            return
    _ensure_active_name(self, 'FACE', allow_write=True)


class EFG_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    edge_prefix: bpy.props.StringProperty(
        name="Edge group prefix",
        default="edge_group",
    )
    face_prefix: bpy.props.StringProperty(
        name="Face group prefix",
        default="face_group",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "edge_prefix")
        layout.prop(self, "face_prefix")


class EFG_UL_edge_groups(bpy.types.UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = []
        flt_neworder = []
        for item in items:
            flt_flags.append(self.bitflag_filter_item if _is_edge_group(item) else 0)
        return flt_flags, flt_neworder

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item is None:
            layout.label(text="")
            return
        if getattr(item, "is_internal", False) or getattr(item, "is_builtin", False):
            layout.label(text=item.name, icon='EDGESEL')
        else:
            layout.prop(item, "name", text="", emboss=False, icon='EDGESEL')


class EFG_UL_face_groups(bpy.types.UIList):
    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = []
        flt_neworder = []
        for item in items:
            flt_flags.append(self.bitflag_filter_item if _is_face_group(item) else 0)
        return flt_flags, flt_neworder

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item is None:
            layout.label(text="")
            return
        if getattr(item, "is_internal", False) or getattr(item, "is_builtin", False):
            layout.label(text=item.name, icon='FACESEL')
        else:
            layout.prop(item, "name", text="", emboss=False, icon='FACESEL')


class EFG_OT_edge_group_add(bpy.types.Operator):
    bl_idname = "efg.edge_group_add"
    bl_label = "Add Edge Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        edge_prefix, _ = _get_prefixes()
        name = _unique_name(edge_prefix, {a.name for a in mesh.attributes})
        mesh.attributes.new(name=name, type='FLOAT', domain='EDGE')
        mesh.edge_group_active_name = name
        mesh.edge_group_index = mesh.attributes.find(name)
        _ensure_active_name(mesh, 'EDGE', allow_write=True)
        return {'FINISHED'}


class EFG_OT_face_group_add(bpy.types.Operator):
    bl_idname = "efg.face_group_add"
    bl_label = "Add Face Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        _, face_prefix = _get_prefixes()
        name = _unique_name(face_prefix, {a.name for a in mesh.attributes})
        mesh.attributes.new(name=name, type='FLOAT', domain='FACE')
        mesh.face_group_active_name = name
        mesh.face_group_index = mesh.attributes.find(name)
        _ensure_active_name(mesh, 'FACE', allow_write=True)
        return {'FINISHED'}


class EFG_OT_edge_group_remove(bpy.types.Operator):
    bl_idname = "efg.edge_group_remove"
    bl_label = "Remove Edge Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = context.object.data
        attr = _get_active_attr(mesh, 'EDGE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        try:
            mesh.attributes.remove(attr)
        except RuntimeError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        _ensure_active_name(mesh, 'EDGE', allow_write=True)
        return {'FINISHED'}


class EFG_OT_face_group_remove(bpy.types.Operator):
    bl_idname = "efg.face_group_remove"
    bl_label = "Remove Face Group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mesh = context.object.data
        attr = _get_active_attr(mesh, 'FACE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        try:
            mesh.attributes.remove(attr)
        except RuntimeError as exc:
            self.report({'WARNING'}, str(exc))
            return {'CANCELLED'}
        _ensure_active_name(mesh, 'FACE', allow_write=True)
        return {'FINISHED'}


class EFG_OT_edge_group_assign(bpy.types.Operator):
    bl_idname = "efg.edge_group_assign"
    bl_label = "Assign"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'EDGE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.edges.layers.float.get(attr.name)
        if layer is None:
            layer = bm.edges.layers.float.new(attr.name)
        weight = context.scene.edge_group_weight
        for e in bm.edges:
            if e.select:
                e[layer] = weight
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_edge_group_remove_assign(bpy.types.Operator):
    bl_idname = "efg.edge_group_remove_assign"
    bl_label = "Remove"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'EDGE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.edges.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for e in bm.edges:
            if e.select:
                e[layer] = 0.0
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_edge_group_select(bpy.types.Operator):
    bl_idname = "efg.edge_group_select"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'EDGE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.edges.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for e in bm.edges:
            if e[layer] > 0.0:
                e.select = True
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_edge_group_deselect(bpy.types.Operator):
    bl_idname = "efg.edge_group_deselect"
    bl_label = "Deselect"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'EDGE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.edges.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for e in bm.edges:
            if e[layer] > 0.0:
                e.select = False
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_face_group_assign(bpy.types.Operator):
    bl_idname = "efg.face_group_assign"
    bl_label = "Assign"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'FACE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.faces.layers.float.get(attr.name)
        if layer is None:
            layer = bm.faces.layers.float.new(attr.name)
        weight = context.scene.face_group_weight
        for f in bm.faces:
            if f.select:
                f[layer] = weight
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_face_group_remove_assign(bpy.types.Operator):
    bl_idname = "efg.face_group_remove_assign"
    bl_label = "Remove"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'FACE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.faces.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for f in bm.faces:
            if f.select:
                f[layer] = 0.0
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_face_group_select(bpy.types.Operator):
    bl_idname = "efg.face_group_select"
    bl_label = "Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'FACE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.faces.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for f in bm.faces:
            if f[layer] > 0.0:
                f.select = True
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class EFG_OT_face_group_deselect(bpy.types.Operator):
    bl_idname = "efg.face_group_deselect"
    bl_label = "Deselect"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        attr = _get_active_attr(mesh, 'FACE', allow_write=True)
        if not attr:
            return {'CANCELLED'}
        if obj.mode != 'EDIT':
            self.report({'WARNING'}, "Edit mode required")
            return {'CANCELLED'}
        bm = bmesh.from_edit_mesh(mesh)
        layer = bm.faces.layers.float.get(attr.name)
        if layer is None:
            return {'CANCELLED'}
        for f in bm.faces:
            if f[layer] > 0.0:
                f.select = False
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        return {'FINISHED'}


class DATA_PT_edge_groups(bpy.types.Panel):
    bl_label = "Edge Groups"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mesh = obj.data

        row = layout.row()
        row.template_list("EFG_UL_edge_groups", "", mesh, "attributes", mesh, "edge_group_index", rows=4)

        col = row.column(align=True)
        col.operator("efg.edge_group_add", icon='ADD', text="")
        col.operator("efg.edge_group_remove", icon='REMOVE', text="")

        if obj.mode == 'EDIT':
            layout.prop(context.scene, "edge_group_weight", text="Weight", slider=True)

            row = layout.row(align=True)
            row.operator("efg.edge_group_assign", text="Assign")
            row.operator("efg.edge_group_remove_assign", text="Remove")
            row = layout.row(align=True)
            row.operator("efg.edge_group_select", text="Select")
            row.operator("efg.edge_group_deselect", text="Deselect")


class DATA_PT_face_groups(bpy.types.Panel):
    bl_label = "Face Groups"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = context.object
        mesh = obj.data

        row = layout.row()
        row.template_list("EFG_UL_face_groups", "", mesh, "attributes", mesh, "face_group_index", rows=4)

        col = row.column(align=True)
        col.operator("efg.face_group_add", icon='ADD', text="")
        col.operator("efg.face_group_remove", icon='REMOVE', text="")

        if obj.mode == 'EDIT':
            layout.prop(context.scene, "face_group_weight", text="Weight", slider=True)

            row = layout.row(align=True)
            row.operator("efg.face_group_assign", text="Assign")
            row.operator("efg.face_group_remove_assign", text="Remove")
            row = layout.row(align=True)
            row.operator("efg.face_group_select", text="Select")
            row.operator("efg.face_group_deselect", text="Deselect")


classes = (
    EFG_Preferences,
    EFG_UL_edge_groups,
    EFG_UL_face_groups,
    EFG_OT_edge_group_add,
    EFG_OT_edge_group_remove,
    EFG_OT_edge_group_assign,
    EFG_OT_edge_group_remove_assign,
    EFG_OT_edge_group_select,
    EFG_OT_edge_group_deselect,
    EFG_OT_face_group_add,
    EFG_OT_face_group_remove,
    EFG_OT_face_group_assign,
    EFG_OT_face_group_remove_assign,
    EFG_OT_face_group_select,
    EFG_OT_face_group_deselect,
    DATA_PT_edge_groups,
    DATA_PT_face_groups,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Mesh.edge_group_index = bpy.props.IntProperty(update=_update_active_edge_index)
    bpy.types.Mesh.edge_group_active_name = bpy.props.StringProperty()
    bpy.types.Mesh.face_group_index = bpy.props.IntProperty(update=_update_active_face_index)
    bpy.types.Mesh.face_group_active_name = bpy.props.StringProperty()

    bpy.types.Scene.edge_group_weight = bpy.props.FloatProperty(
        name="Edge Group Weight",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )
    bpy.types.Scene.face_group_weight = bpy.props.FloatProperty(
        name="Face Group Weight",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Mesh.edge_group_index
    del bpy.types.Mesh.edge_group_active_name
    del bpy.types.Mesh.face_group_index
    del bpy.types.Mesh.face_group_active_name
    del bpy.types.Scene.edge_group_weight
    del bpy.types.Scene.face_group_weight


if __name__ == "__main__":
    register()
