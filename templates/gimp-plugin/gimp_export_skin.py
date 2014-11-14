#! /usr/bin/env python
# This lists the layers of a GIMP xcf file.  This also exports the visible layers into a png file.
#
# Execute the commands:
#
#   curl -O https://bitbucket.org/rgl/make_dmg/downloads/background.xcf
#   gimp -idf --batch-interpreter=python-fu-eval -b - -b 'pdb.gimp_quit(0)' < gimp_xcf_list_layers.py
#
# See http://www.gimp.org/docs/python/
# See http://gimpbook.com/scripting/
#
# -- Rui Lopes (ruilopes.com)
import re
import sys
import os
import json
from pipes import quote
from string import Template

LAYOUT = Template("""
parts {
   device {
        display {
            width   ${screen_port_width}
            height  ${screen_port_height}
            x       0
            y       0
        }
    }
    
    portrait {
        background {
            image   background_port.png
        }

        buttons {
            ${buttons_port}
        }
    }
    
    landscape {
        background {
            image   background_land.png
        }

        buttons {
            ${buttons_land}
        }
    }
}

layouts {
    portrait {
        width     ${background_port_width}
        height    ${background_port_height} 
        color     0x555555
        
        part1 {
            name    portrait
            x       0
            y       0
        }

        part2 {
            name    device
            x       $screen_port_x
            y       $screen_port_y
        }
    }
    
    landscape {
        width     ${background_land_width}
        height    ${background_land_height}
        color     0x555555
        
        part1 {
            name    landscape
            x       0
            y       0
        }

        part2 {
            name   device
            x      $screen_land_x
            y      $screen_land_y
            rotation 3
        }
    }
}

""")

BUTTON = Template("""
            ${button_name} {
                image   ${button_name}_${orientation}.png
                x       ${button_x}
                y       ${button_y}
            }""")

def convert_skin_layout(source, destination):

    with open(source, 'r') as f:
        layout = json.loads(f.read())
 
    image = layout['image']
    layers = layout['layers']
    background = dict(land = layers.pop('background_land.png'), port = layers.pop('background_port.png'))
    screen_land = layers.pop('screen_land.png')
    screen_port = layers.pop('screen_port.png')
    buttons = dict(land = [],port = [])

    offset_x = lambda layer,orientation: layer['offsets'][0] - background[orientation]['offsets'][0]
    offset_y = lambda layer,orientation: layer['offsets'][1] - background[orientation]['offsets'][1]

    fullname_parser = re.compile('^(.*)_(\w*)\.?.*$')
    for layername,layer in layers.iteritems():
        button_name, orientation = fullname_parser.findall(layername)[0]
        orientation = orientation[:4].lower()
        buttons[orientation].append(BUTTON.substitute({'button_name':button_name,'orientation':orientation,'button_x':offset_x(layer, orientation),'button_y':offset_y(layer, orientation)}))
        
    with open(destination, 'w') as f:

        f.write(LAYOUT.substitute(
            {
            'background_port_width':background['port']['width'],
            'background_port_height':background['port']['height'],
            'background_land_width':background['land']['width'],
            'background_land_height':background['land']['height'],

            'screen_port_width':screen_port['width'],
            'screen_port_height':screen_port['height'],

            'screen_port_x':offset_x(screen_port,'port'),
            'screen_port_y':offset_y(screen_port,'port'),
            'screen_land_x':offset_x(screen_land,'land'),
            'screen_land_y':offset_y(screen_land,'land') + screen_land['height'],

            'buttons_land':''.join(buttons['land']),
            'buttons_port':''.join(buttons['port']),
            }
        ))

def flatten_layers(drawable, visible=True):
    for layer in drawable.layers:
        layer_visible = visible and layer.visible
        if not hasattr(layer, 'layers'):
            yield (layer, layer_visible)
            continue
        for l in flatten_layers(layer, layer_visible):
            yield l

def extract_layers(image, layer, save_path):

    layers = list(flatten_layers(image))
    
    print 'IMAGE_HEADER width height'
    print "IMAGE", image.width, image.height
    layout = {'image':None, 'layers':None}
    layout['image'] = {'name':image.name, 'width':image.width, 'height':image.height}
    layout['layers'] = {}
    
    print 'LAYER_HEADER visible x y width height name'
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    pdb.gimp_image_undo_disable(image)
    
    for layer, visible in layers:
        print "LAYER", visible and "1" or "0", layer.offsets[0], layer.offsets[1], layer.width, layer.height, layer.name
    
        if not visible:
            continue
        
        if pdb.gimp_item_is_text_layer(layer):
            with open(os.path.join(save_path,layer.name),'w') as f:
                f.write(pdb.gimp_text_layer_get_text(layer))
        else:
            layout["layers"].setdefault(layer.name, {'offsets':layer.offsets, 'width':layer.width, 'height':layer.height})
    
            png_filepath = os.path.join(save_path, layer.name)
    
            pdb.file_png_save2(
                image,
                layer,
                png_filepath,
                png_filepath,
                0,  # interlacing (Adam7)
                9,  # compression level (0-9)
                0,  # save background color
                0,  # save gamma
                0,  # save layer offset
                1,  # save resolution
                0,  # save creation time
                0,  # save comment 
                1   # save color values from transparent pixels
            )
    
    # Write json layout
    layout_json = os.path.join(save_path,'layout.json')
    with open(layout_json, 'w') as f:
        f.write(json.dumps(layout, indent=2))

    # Write emulator skin layout
    layout_skin = os.path.join(save_path,'layout')
    convert_skin_layout(layout_json, layout_skin)

if __name__=='__main__':

    try:
        pdb
        interactive = False
    except NameError, e:
        interactive = True
    
    if not interactive:
        xcf_path = os.environ.get('XCF_FILE')
        if xcf_path:
            png_path = os.path.splitext(xcf_path)[0]
            image = pdb.gimp_xcf_load(0, xcf_path, xcf_path)
            extract_layers(image, None, png_path)

    else:
        import gimpfu
        pdb = gimpfu.pdb
        DEFAULT_OUTPUT_DIR = os.getcwd()
        gimpfu.register("python_fu_extract", 
                        "Extract Layers", 
                        "Save coordinates to json file", 
                        "Nic", "Nicolas CORNETTE", "2014", 
                        "<Image>/File/Export/Export Emulator Skin...", 
                        "*", [
                            (gimpfu.PF_DIRNAME, "save-path", "Path for export", DEFAULT_OUTPUT_DIR),
                              ], 
                        [], 
                        extract_layers) #, menu, domain, on_query, on_run)
        gimpfu.main()

