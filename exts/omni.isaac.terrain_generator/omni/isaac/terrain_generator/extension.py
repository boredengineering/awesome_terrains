import omni.ext
import omni.ui as ui

from .terrain_utils import *
from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from omni.isaac.core.utils.prims import define_prim, get_prim_at_path
import omni.usd

# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[omni.isaac.terrain_generator] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class OmniIsaacTerrain_generatorExtension(omni.ext.IExt):
    
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[omni.isaac.terrain_generator] omni isaac terrain_generator startup")

        self._count = 0

        self._window = ui.Window("My Window", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")


                def on_click():
                    self.get_terrain()
                    # self._count += 1
                    label.text = "Generate Terrain"

                def on_reset():
                    self.clear_terrain()
                    # self._count = 0
                    label.text = "Clear Stage"

                on_reset()

                with ui.HStack():
                    ui.Button("Add Terrain", clicked_fn=on_click)
                    ui.Button("Clear Stage", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[omni.isaac.terrain_generator] omni isaac terrain_generator shutdown")

    # This deletes the terrain
    def clear_terrain(self):
        current_stage = get_current_stage()
        current_stage.RemovePrim("/World/terrain")
    
    # The stuff that makes terrain
    def get_terrain(self):
        stage = get_current_stage()
        # create all available terrain types
        num_terains = 8
        terrain_width = 12.
        terrain_length = 12.
        horizontal_scale = 0.25  # [m]
        vertical_scale = 0.005  # [m]
        num_rows = int(terrain_width/horizontal_scale)
        num_cols = int(terrain_length/horizontal_scale)
        heightfield = np.zeros((num_terains*num_rows, num_cols), dtype=np.int16)

        def new_sub_terrain(): 
            return SubTerrain(width=num_rows, length=num_cols, vertical_scale=vertical_scale, horizontal_scale=horizontal_scale)

        # weird
        heightfield[0:num_rows, :] = random_uniform_terrain(new_sub_terrain(), min_height=-0.2, max_height=0.2, step=0.2, downsampled_scale=0.5).height_field_raw
        # Make a plain slope, need to understand how to control. When deleted makes a flat terrain
        heightfield[num_rows:2*num_rows, :] = sloped_terrain(new_sub_terrain(), slope=-0.5).height_field_raw
        # Pyramid slope, probably the base for the stairs code
        heightfield[2*num_rows:3*num_rows, :] = pyramid_sloped_terrain(new_sub_terrain(), slope=-0.5).height_field_raw
        # nice square obstacles randomly generated
        heightfield[3*num_rows:4*num_rows, :] = discrete_obstacles_terrain(new_sub_terrain(), max_height=0.5, min_size=1., max_size=5., num_rects=20).height_field_raw
        # Nice curvy terrain
        heightfield[4*num_rows:5*num_rows, :] = wave_terrain(new_sub_terrain(), num_waves=2., amplitude=1.).height_field_raw
        # Adjust stair step size, how far it goes down or up.
        heightfield[5*num_rows:6*num_rows, :] = stairs_terrain(new_sub_terrain(), step_width=0.75, step_height=-0.5).height_field_raw
        # Need to figure out how to cahnge step heights and make a Pyramid Stair go up
        heightfield[6*num_rows:7*num_rows, :] = pyramid_stairs_terrain(new_sub_terrain(), step_width=0.75, step_height=-0.5).height_field_raw
        # Stepping Stones need fixing depth
        heightfield[7*num_rows:8*num_rows, :] = stepping_stones_terrain(new_sub_terrain(), stone_size=1., stone_distance=1., max_height=0.5, platform_size=0.).height_field_raw
        
        vertices, triangles = convert_heightfield_to_trimesh(heightfield, horizontal_scale=horizontal_scale, vertical_scale=vertical_scale, slope_threshold=1.5)

        position = np.array([-6.0, 48.0, 0])
        orientation = np.array([0.70711, 0.0, 0.0, -0.70711])
        add_terrain_to_stage(stage=stage, vertices=vertices, triangles=triangles, position=position, orientation=orientation)

# Error
# Cannot load DefinePrim
#   File "e:\bored engineer github\bored engineer\awesome_terrains\exts\omni.isaac.terrain_generator\omni\isaac\terrain_generator\extension.py", line 4, in <module>
#     from .terrain_utils import *
#   File "e:\bored engineer github\bored engineer\awesome_terrains\exts\omni.isaac.terrain_generator\omni\isaac\terrain_generator\terrain_utils.py", line 384, in <module>
#     terrain = add_terrain_to_stage(stage, vertices, triangles)
#   File "e:\bored engineer github\bored engineer\awesome_terrains\exts\omni.isaac.terrain_generator\omni\isaac\terrain_generator\terrain_utils.py", line 340, in add_terrain_to_stage
#     terrain_mesh = stage.DefinePrim("/World/terrain", "Mesh")
# AttributeError: 'NoneType' object has no attribute 'DefinePrim'