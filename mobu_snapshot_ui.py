# @Jiapei Lu 2025.5.17


from pyfbsdk import *
from pyfbsdk_additions import *
import json

SNAPSHOT_NULL_NAME = "AnimSnapshotNull"

playercontrol = FBPlayerControl()
def sync_ik_fk():
    if not FBApplication().CurrentCharacter:
        return
    
    if not get_selected_models():
        return
    time_span = FBSystem().CurrentTake.LocalTimeSpan
    #ts_time = time_span.GetStart()
    te_time = time_span.GetStop()
    ct_time = FBSystem().LocalTime
    nt_time = te_time
    while ct_time != nt_time:
        ct_time = FBSystem().LocalTime
        playercontrol.Key()
        playercontrol.GotoNextKey ()
        FBSystem().Scene.Evaluate()
        nt_time = FBSystem().LocalTime
        #print(ct_time.GetFrame(),nt_time.GetFrame())

def get_snapshot_null():
    scene = FBSystem().Scene
    for comp in scene.Components:
        if isinstance(comp, FBModel) and comp.Name == SNAPSHOT_NULL_NAME:
            return comp
    

def create_snapshot_null():
    is_snapshot_null = get_snapshot_null()
    if is_snapshot_null:
        is_snapshot_null.FBDelete()
    null_model = FBModelNull(SNAPSHOT_NULL_NAME)
    return null_model


def read_snapshot_animable_nodes():
    nodes={}
    snapshot_null = get_snapshot_null()
    if not snapshot_null:
        return
    animable_nodes = snapshot_null.PropertyList
    if not animable_nodes:
        return
    return [ node for node in snapshot_null.PropertyList if node.IsUserProperty()]
    # I don't have brain for this...
    #[ nodes.setdefault( '' , node) node for node in snapshot_null.PropertyList if node.IsUserProperty()]
    
    
def get_selected_models():
    models = FBModelList()
    FBGetSelectedModels(models)
    return models


def get_model_anim_nodes(model):
    animNodes= set()
    for prop in model.PropertyList:
        if prop.IsAnimatable():
            animNode = prop.GetAnimationNode()
            if animNode and animNode.KeyCount > 0:
                animNodes.add(prop)
    return animNodes


def get_namespace_from_first_selected()->str:
    selected_models = get_selected_models()
    if not selected_models:
        print('Select a model comewith namespace')
        return
    ns = selected_models[0].OwnerNamespace
    if not ns:
        print("Can't get namespace for selected model")
        return
    return ns


def deserialize_snapshot_porperty_name(node):
    model_name, attr_name = node.Name.split(":")
    return model_name, attr_name

        
def apply_snapshot_from_property(withSelNameSpace = True, fullPose = True):
    snapshot_animable_nodes = read_snapshot_animable_nodes()
    if not snapshot_animable_nodes:
        return

    ns = None
    if withSelNameSpace:
        ns = get_namespace_from_first_selected()
        if not ns:
            FBMessageBox("錯誤", f"未選擇有Namespace物件", "OK")
            return  
    
    if fullPose:
        for animable_node in snapshot_animable_nodes:
            model_name, attr_name =deserialize_snapshot_porperty_name(animable_node)
            if ns:
                model_name = f'{ns.Name}:{model_name}'
            model = FBFindModelByLabelName(model_name)
            if not model:
                print(f"Can't find model: {model_name}")
                continue
            target_node = model.PropertyList.Find(attr_name)
            if not target_node:
                continue
            insert_animfcurve(animable_node, target_node)
            
        FBMessageBox("完成", "動畫已從 Null 貼上", "OK")
    
    else:
        selected_models = get_selected_models()
        if not selected_models:
            print('Select a model comewith namespace')
            return
        for model in selected_models:
            animable_nodes = [ node for node in snapshot_animable_nodes if node.Name.startswith(model.Name)]
            if not animable_nodes:
                print(f"Cant' find keydata for {model.Name!r}")
                continue
            for animable_node in animable_nodes:
                model_name, attr_name =deserialize_snapshot_porperty_name(animable_node)
                target_node = model.PropertyList.Find(attr_name)
                if target_node:
                    copy_animfcurve(animable_node, target_node)
                    
        FBMessageBox("完成", "動畫已從 Null 貼上", "OK")


def mark_nonkey_section(fcurve:FBFCurve):
    s_time = fcurve.Keys[0].Time
    start_frame = s_time.GetFrame()
    e_time = fcurve.Keys[-1].Time
    last_frame = e_time.GetFrame()
    # 取得最後一格的時間（結束時間）
    time_span = FBSystem().CurrentTake.LocalTimeSpan
    ts_time = time_span.GetStart()
    te_time = time_span.GetStop()
    
    if te_time > e_time:
        last_frame = te_time.GetFrame()
    if ts_time < s_time:
        start_frame = ts_time.GetFrame()
        
    s_ranges= set(key.Time.GetFrame() for key in fcurve.Keys)
    f_ranges= set(range(start_frame, last_frame))
    rv =get_non_continuous_ranges( list( f_ranges-s_ranges ))

    if rv:
        return rv
    
from itertools import groupby

def get_non_continuous_ranges(lst):
    ranges = []
    for _, group in groupby(enumerate(lst), lambda x: x[1] - x[0]):
        group = list(group)
        if len(group) > 1:
            ranges.append((group[0][1], group[-1][1]))
        else:
            ranges.append((group[0][1],group[0][1]))
    return ranges
                        
def clear_extra_keys(withSelNameSpace = True, fullPose = True):
    snapshot_animable_nodes = read_snapshot_animable_nodes()
    if not snapshot_animable_nodes:
        return

    ns = None
    if withSelNameSpace:
        ns = get_namespace_from_first_selected()
        if not ns:
            FBMessageBox("錯誤", f"未選擇有Namespace物件", "OK")
            return
    
    if fullPose:
        for animable_node in snapshot_animable_nodes:
            model_name, attr_name =deserialize_snapshot_porperty_name(animable_node)
            if ns:
                model_name = f'{ns.Name}:{model_name}'
            model = FBFindModelByLabelName(model_name)
            if not model:
                print(f"Can't find model: {model_name}")
                continue
            target_node = model.PropertyList.Find(attr_name)
            if target_node:
                for s,t in zip(animable_node.GetAnimationNode().Nodes,target_node.GetAnimationNode().Nodes):
                    t_times = set(key.Time.Get() for key in t.FCurve.Keys)
                    s_times = set(key.Time.Get() for key in s.FCurve.Keys)
                    r_times = t_times - s_times
                    non_frames_section = mark_nonkey_section(s.FCurve)
                    if not non_frames_section:
                        continue
                    for s,e in non_frames_section:
                        time = FBTime(0,0,0,s)
                        t.FCurve.KeyDelete(FBTime(0,0,0,s),FBTime(0,0,0,e))
    
            #FBMessageBox("完成", f"多餘關鍵幀已從 {model_name} 清除", "OK")
        FBMessageBox("完成", f"多餘關鍵幀已清除", "OK")
        
        
def save_snapshot_to_null_property():
    selected_models = get_selected_models()
    if not selected_models:
        FBMessageBox("Warning", "請先選取模型", "OK")
        return

    snapshot_null = create_snapshot_null()
    all_data = {}

    for model in selected_models:
        nodes = get_model_anim_nodes(model)
        if not nodes:
                continue
        for node in nodes:
            prop_name = ':'.join((model.Name,node.Name))
            prop = snapshot_null.PropertyList.Find(prop_name)
            if not prop:
                prop =add_sanpshot_prop(snapshot_null, node, prop_name)
                prop.SetAnimated(True)
            copy_animfcurve(node, prop)
                
    FBMessageBox("完成", f"快照已儲存至 {SNAPSHOT_NULL_NAME!r} 的屬性中", "OK")


def add_sanpshot_prop(snapshot_null, ref_source, prop_name):
    if isinstance( ref_source, FBPropertyAnimatableVector3d ):
        return snapshot_null.PropertyCreate(prop_name, FBPropertyType.kFBPT_Vector3D, "", True, True, None)
    
    
def copy_animfcurve(source, target):
    if isinstance( source, FBPropertyAnimatableVector3d ):
        for s,t in zip(source.GetAnimationNode().Nodes,target.GetAnimationNode().Nodes):
            t.FCurve.KeyReplaceBy(s.FCurve)


def create_snapshot_ui():
    t = FBCreateUniqueTool("Anim Snapshot(Beta)")
    t.StartSizeX = 220
    t.StartSizeY = 220
    vbox = FBVBoxLayout()

    b_apply = FBButton()
    b_apply.Caption = "Sync Keyframe FK/IK"
    b_apply.OnClick.Add(lambda control, event: sync_ik_fk())
    vbox.Add(b_apply, 30)

    b_save = FBButton()
    b_save.Caption = "Save Anim Snapshot"
    b_save.OnClick.Add(lambda control, event: save_snapshot_to_null_property())
    vbox.Add(b_save, 30)

    b_apply = FBButton()
    b_apply.Caption = "Paste Full Anim"
    b_apply.OnClick.Add(lambda control, event: apply_snapshot_from_property())
    vbox.Add(b_apply, 30)

    b_apply = FBButton()
    b_apply.Caption = "Paste Sel Anim"
    b_apply.OnClick.Add(lambda control, event: apply_snapshot_from_property(fullPose = False))
    vbox.Add(b_apply, 30)

    b_clear = FBButton()
    b_clear.Caption = "Clearn Extra Keys"
    b_clear.OnClick.Add(lambda control, event: clear_extra_keys())
    vbox.Add(b_clear, 30)

    x = FBAddRegionParam(10,FBAttachType.kFBAttachLeft,"")
    y = FBAddRegionParam(10,FBAttachType.kFBAttachTop,"")
    w = FBAddRegionParam(-10,FBAttachType.kFBAttachRight,"")
    h = FBAddRegionParam(-10,FBAttachType.kFBAttachBottom,"")

    t.AddRegion("main", "main", x, y, w, h)
    t.SetControl("main", vbox)
    ShowTool(t)

if __name__ == "__main__" or "builtins":
    create_snapshot_ui()
