bl_info = {"name": "Template", "category": "Node"}
import copy
import math
import bpy
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatProperty, FloatVectorProperty, CollectionProperty, BoolProperty
from bpy.types import NodeTree, Node, NodeLinks, NodeSocket, PropertyGroup 
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

class NetworkNodeTree(NodeTree):
    """Network Node Tree"""
    bl_idname = "NetworkNodeTree"
    bl_label = "Network Node Tree"
    bl_icon = "NODETREE"

    customData = {'NodeTree':bl_idname}

    def write_data(sender, name, thing):
        if sender in NetworkNodeTree.customData:
            NetworkNodeTree.customData[sender][name] = thing
        else:
            NetworkNodeTree.customData[sender] = {}
            NetworkNodeTree.customData[sender][name] = thing

    def read_data(sender, name):
        if sender in NetworkNodeTree.customData:
            if name in NetworkNodeTree.customData[sender]:
                return NetworkNodeTree.customData[sender][name]
        return None

    @classmethod
    def poll(cls, ntree):
        return True

class SynapseProperty(PropertyGroup):
    parent = StringProperty() #Parent node name 
    call = StringProperty(default = "uda") #Parent node update function name

    def uda(self, context):
        if self.parent in self.id_data.nodes:
            if hasattr(self.id_data.nodes[self.parent], self.call):
                getattr(self.id_data.nodes[self.parent], self.call)(context)

    def callback(self, name, call):
        self.parent = name
        self.call = call

    #Custom properties are basically a struct, you can have any number of built in (bpy) datatypes defined here:
    value = FloatProperty(default = 1.0, update=uda)
    weight = FloatProperty(default = 1.0, update=uda)

    def template_layout(self, layout):
        row = layout.row(align=True)
        row.label("Value")
        row.prop(self, "value", text="")

class SynapseSocket(NodeSocket):
    """Synapse Socket"""
    bl_idname = "SynapseSocket"
    bl_label = "Synapse"

    default_value = bpy.props.PointerProperty(type=SynapseProperty) 

    def callback(self, name, call):
        self.default_value.callback(name, call)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            self.default_value.template_layout(layout)

    def draw_color(self, context, node):
        return(1.0,0.4,0.2,1.0)

class NeuronNode(Node, NetworkNodeTree):
    """Neuron Node"""
    bl_idname = "NeuronNode"
    bl_label = "Neuron"
    bl_icon = "OBJECT_DATA"

    # Update callback for properties defined within this node
    def uda(self, context):
        self.update()

    # Property that is not attached to a socket
    numInputsProperty = IntProperty(name="numInputsProperty", default=1, update=uda)

    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node, as shown below.
    # NOTE: this is not the same as the standard __init__ function in Python, which is
    #       a purely internal Python method and unknown to the node system!
    def init(self, context):
        self.inputs.new("SynapseSocket", "Value 1").callback(self.name, "uda")
        self.inputs.new("SynapseSocket", "Value 2").callback(self.name, "uda")
        self.inputs.new("SynapseSocket", "Value 3").callback(self.name, "uda")
        self.inputs.new("SynapseSocket", "Value 4").callback(self.name, "uda")
        self.inputs.new("SynapseSocket", "Value 5").callback(self.name, "uda")
        self.inputs.new("SynapseSocket", "Value 6").callback(self.name, "uda")
        #self.inputs.new("NodeSocketInt", "New")
        self.outputs.new("SynapseSocket", "Output")

    def get_value(self, name):
        inp = None
        if self.inputs[name].is_linked and self.inputs[name].links[0].is_valid:
            inp = self.inputs[name].links[0].from_socket.default_value
        else:
            inp = self.inputs[name].default_value
        return inp

    def update_chain(self, name):
        if self.outputs[name].is_linked:
            for link in self.outputs[name].links:
                if link.is_valid:
                    link.to_node.update()

    def check_new(self):
        if len(self.inputs) > self.numInputsProperty:
            self.inpputs.clear()
        while len(self.inputs) < self.numInputsProperty:
            num = len(self.inputs)
            self.inputs.new("SynapseSocket", "Value "+str(num))

    def sum_inputs(self):
        runTot = 0
        for name in self.inputs.keys():
            runTot += self.get_value(name).value * self.get_value(name).weight
        return runTot

    def update(self):
        #self.check_new()
        self.outputs["Output"].default_value.value = self.sum_inputs()
        print("update")
        self.update_chain("Output")

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.label("Output: " + str("%.3f" % self.sum_inputs()))
        layout.label("Neuron Settings")
        #layout.prop(self, "numInputsProperty")

    # Detail buttons in the sidebar.
    # If this function is not defined, the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "numInputsProperty")

    def draw_label(self):
        return "Neuron"

class NeuralOutputNode(Node, NetworkNodeTree):
    """Neural Output Node"""
    bl_idname = "NeuralOutputNode"
    bl_label = "Neural Output"
    bl_icon = "OBJECT_DATA"

    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node, as shown below.
    # NOTE: this is not the same as the standard __init__ function in Python, which is
    #       a purely internal Python method and unknown to the node system!
    def init(self, context):
        self.inputs.new("SynapseSocket", "Value")

    # Update callback for properties defined within this node
    def uda(self, context):
        self.update()

    # Property that is not attached to a socket
    outputProperty = FloatProperty(name="outputProperty", default=0.0, update=uda)

    def get_value(self, name):
        inp = None
        if self.inputs[name].is_linked and self.inputs[name].links[0].is_valid:
            inp = self.inputs[name].links[0].from_socket.default_value
        else:
            inp = self.inputs[name].default_value
        return inp

    def update_chain(self, name):
        if self.outputs[name].is_linked:
            for link in self.outputs[name].links:
                if link.is_valid:
                    link.to_node.update()

    def update(self):
        self.outputProperty = self.get_value("Value").value
        #self.check_new()
        print("update")

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.label("Neuron Settings")
        layout.prop(self, "outputProperty")

    # Detail buttons in the sidebar.
    # If this function is not defined, the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "outputProperty")

    def draw_label(self):
        return "Output"

class ABCCustomNodeCategory(NodeCategory):
    @classmethod
    def poll(cls,context):
        return True #context.space_data.tree_type == "ABCCustomNodeCategory"

node_categories = [
    ABCCustomNodeCategory(
        "CUSTOM",
        "Custom",
        items = [
            NodeItem("NeuronNode"),
            NodeItem("NeuralOutputNode")
        ]
    )
]

registered = False

def register():
    bpy.utils.register_class(NetworkNodeTree)
    bpy.utils.register_class(SynapseProperty)
    bpy.utils.register_class(SynapseSocket)
    bpy.utils.register_class(NeuronNode)
    bpy.utils.register_class(NeuralOutputNode)
    nodeitems_utils.register_node_categories("CUSTOM", node_categories)
    registered = True

def unregister(): 
    nodeitems_utils.unregister_node_categories("CUSTOM")
    bpy.utils.unregister_class(NetworkNodeTree)
    bpy.utils.unregister_class(SynapseProperty)
    bpy.utils.unregister_class(SynapseSocket)
    bpy.utils.unregister_class(NeuronNode)
    bpy.utils.unregister_class(NeuralOutputNode)
    registered = False

if __name__ == "__main__" :  
    if registered:
        unregister()
    try:
        register()
    except:
        print("failed to register")