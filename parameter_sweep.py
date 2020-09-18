#Author-Clark Teeple
#Description-Programatically generate and export tauruses of different aspect ratios
#   USAGE: Place 'permute: #,#,#' in the comment of any parameter you want to permute over.

import adsk.core, adsk.fusion, adsk.cam, traceback
import os
import itertools 


def select_base_folder(ui,start_path=None):
    settings_directory = os.path.dirname(os.path.realpath(__file__))
    settings_file = os.path.join(settings_directory,'save_paths.cfg')

    if start_path:
        pass        
    elif os.path.exists(settings_file):
        with open(settings_file, 'r') as file:
            start_path = file.readline()
    else:
        start_path = os.path.expanduser("~")
    
    if not os.path.exists(start_path):
        os.makedirs(start_path)
    
    
    # Set styles of file dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Select where you want to save your STL files'
    folderDlg.initialDirectory	= start_path
    
    # Show folder dialog
    folder = start_path
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        folder = folderDlg.folder


    if not os.path.exists(folder):
            os.makedirs(folder)

    with open(settings_file, 'w') as file:
        file.write(folder)

    return folder



def run(context):
    ui = None
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        # Get the root component of the active design
        rootComp = design.rootComponent

        # Specify the folder to write out the results.
        #base_folder = 'C:/temp/STLExport/'
        base_folder = select_base_folder(ui)
        part_name=adsk.core.Application.get().activeDocument.name
        part_name = part_name.replace(" ", "_")
        folder = os.path.join(base_folder, part_name)
        file_base = part_name

        if not os.path.exists(folder):
            os.makedirs(folder)
        

        # Get the parameters named "Length" and "Width" to change.                
        params_to_use = []
        for idx in range(design.allParameters.count):
            param = design.allParameters.item(idx)
            comment = param.comment
            comment = comment.lower()

            # If the paramters is one you want to include in the permutation, move forward.
            if 'permute' in comment or 'sweep' in comment:
                param_dict = dict()
                param_dict['item']=param
                param_dict['name']=param.name

                # Split the parameters into a list
                vals = comment.split(':')
                if len(vals)>1:
                    vals = vals[1] # Get the parameter values after the colon
                    vals = vals.replace(" ", "") # Remove whitespace
                    vals = vals.split(',') # split into a list
                    param_dict['values']= vals

                    if len(vals)>0:
                        params_to_use.append(param_dict)

        # If there are no parameters to permute, then end there.
        if len(params_to_use)==0:
            returnValue = ui.messageBox('No permutable parameters were found. Closing out now.', 'No Params Found')
            return
            

        # Make all permutations of parameters
        all_items = []
        all_vals = []
        all_init_states = []
        for curr_param in params_to_use:
            all_items.append(curr_param['item'])
            all_vals.append(curr_param['values'])
            all_init_states.append(curr_param['item'].expression)

        # Compute all possible permutations 
        parameter_sweep = list(itertools.product(*all_vals))


        param_str = "\n"
        for curr_param in params_to_use:
            param_str+= curr_param['name'] + ': '
            param_str+=" ".join(curr_param['values'])
            param_str+='\n'

        returnValue = ui.messageBox(
            'Using Parameters:\n%s\nThere are %d possible permutations.\n\nDo you want to start permuting?'%(
                param_str, len(parameter_sweep)),
                'Ready to go?',
                adsk.core.MessageBoxButtonTypes.YesNoButtonType)

        if returnValue == 3:
            return

        for row in parameter_sweep:
            file_str = ""
            for idx,val in enumerate(row):
                all_items[idx].expression = val

                file_str += '_'+str(val)

            # Let the view have a chance to paint just so you can watch the progress.
            adsk.doEvents()
                
            # Construct the output filename.
            filename = os.path.join(folder, file_base + file_str + '.stl')
            
            # Save the file as STL.
            exportMgr = adsk.fusion.ExportManager.cast(design.exportManager)
            stlOptions = exportMgr.createSTLExportOptions(rootComp)
            stlOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
            stlOptions.filename = filename
            exportMgr.execute(stlOptions)



        for i, item in enumerate(all_items):
            item.expression = all_init_states[i]

        # Let the view have a chance to paint just so you can watch the progress.
        adsk.doEvents()
                
        ui.messageBox('Finished!')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))