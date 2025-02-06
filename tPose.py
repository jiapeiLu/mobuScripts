from pyfbsdk import *
from pyfbsdk_additions import *

def getGlobalRotate(lModel):
    globalRotation = FBVector3d()
    lModel.GetVector(globalRotation, FBModelTransformationType.kModelRotation, True)
    # print( "Current Global Rotation:", globalRotation)
    return globalRotation

def tPoseAngleMatch(FBVector3d):
    '''
    This function is helping rig to Tpose-ish. Select joints and execute it.
    '''
    for i, angle in enumerate(FBVector3d):
        negative = False
        if angle < 0:
            angle = abs(angle)
            negative = True
        if 0 <= angle < 45:
            angle = 0
        elif 45 <= angle < 135:
            angle = 90
        elif 135 <= angle < 225:
            angle = 180
        elif 225 <= angle < 315:
            angle = 270
        elif 315 <= angle:
            angle = 360
        if negative == True:
            angle = -angle
        FBVector3d[i] = angle
    # set angle
    return FBVector3d

def reurn_HIK_link_model(lCharacter, idName):
    nameId = 'kFB'+idName+'NodeId'
    if nameId in FBBodyNodeId.names.keys():
        model = lCharacter.GetModel(FBBodyNodeId.names[nameId])
        if model:
            return model 

def DOF(lModel,values):
    attrs = ['RotationActive', 'RotationMaxX', 'RotationMaxY',
                'RotationMaxZ', 'RotationMinX', 'RotationMinY', 'RotationMinZ']
    
    for at, v in zip(attrs, values):
        do_exec(lModel, at, v) 

def DOF_Character(lCharacter, Nodes, RotationActive=1, RotationMaxX=1, RotationMaxY=1,RotationMaxZ=0, RotationMinX=1, RotationMinY=1, RotationMinZ=0):
    
    for name in Nodes:
        for side in ['Left', 'Right']:
            values = [RotationActive, RotationMaxX, RotationMaxY,
                        RotationMaxZ, RotationMinX, RotationMinY, RotationMinZ]
            idName = side+name
            model = reurn_HIK_link_model(lCharacter, idName)
            if model:
                DOF(model,values)

def do_exec(model, at, v):
    model = model
    command = "model.{} = {}".format(at, v)
    exec(command)

def T_Pose(lCharacter, is_Finger):
    body = ['Hip', 'Knee', 'Ankle', 'Foot', 'Shoulder', 'Elbow', 'Wrist']
    if is_Finger:
        lThumb = [finger + id for finger in ['Thumb']for id in ['B', 'C', 'D']]
        fingers = [finger + id for finger in ['Index', 'Middle', 'Ring', 'Pinky'] for id in ['A', 'B', 'C', 'D']]
        body = body+lThumb+fingers
    for name in body:
        for side in ['Left', 'Right']:
            node = reurn_HIK_link_model(lCharacter, side+name)
            if node:
                FBSystem().Scene.Evaluate()
                tPoseAngle = tPoseAngleMatch(getGlobalRotate(node))
                node.SetVector(tPoseAngle, FBModelTransformationType.kModelRotation)
    FBSystem().Scene.Evaluate()

def get_select_models():
    lModelList = FBModelList()
    FBGetSelectedModels( lModelList )
    if len( lModelList ) > 0:
        return lModelList

def btn_execute_selection(*args):
    '''select joints and execute this function'''

    lModelList = get_select_models()
    if lModelList:
        for lModel in lModelList:
            if is_Tpose.State:
                tPoseAngle = tPoseAngleMatch(getGlobalRotate(lModel))
                lModel.SetVector(tPoseAngle, FBModelTransformationType.kModelRotation)
            if is_DOF.State:
                DOF(lModel, [1, 1, 1, 0, 1, 1, 0])


def main():
    global is_Tpose, is_DOF
    # Tool creation will serve as the hub for all other controls
    t = FBCreateUniqueTool('Quict T-pose Tool')
    t.StartSizeX = 200
    t.StartSizeY = 160

    # Create a button that is left justify
    x = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
    y = FBAddRegionParam(10, FBAttachType.kFBAttachTop, "")
    w = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")
    h = FBAddRegionParam(-10, FBAttachType.kFBAttachBottom, "")
    t.AddRegion("top", "top", x, y, w, h)
    
    
    box = FBVBoxLayout(FBAttachType.kFBAttachTop)

    hStrip = FBHBoxLayout(FBAttachType.kFBAttachLeft)
    vStrip = FBVBoxLayout(FBAttachType.kFBAttachTop)
    hStrip.Add(vStrip, 20)
    vStrip = FBVBoxLayout(FBAttachType.kFBAttachTop)
    is_Tpose = FBButton()
    is_Tpose.Caption = 'T-Pose'
    is_Tpose.Style = FBButtonStyle.kFBCheckbox
    is_Tpose.State = True
    vStrip.Add(is_Tpose, 20)

    is_DOF = FBButton()
    is_DOF.Caption = 'DOF'
    is_DOF.Style = FBButtonStyle.kFBCheckbox
    is_DOF.State = False
    vStrip.Add(is_DOF, 20)

    hStrip.AddRelative(vStrip, 0.5)  # ====End of hStrip
    box.Add(hStrip, 60)

    bnt03 = FBButton()
    bnt03.Caption = "Execute Selected"
    bnt03.Justify = FBTextJustify.kFBTextJustifyCenter
    box.Add(bnt03, 30, wight=30)
    bnt03.OnClick.Add(btn_execute_selection)
 

    
    t.SetControl("top", box)
    ShowTool(t)

if __name__ in ('__main__', 'builtins'):
    main()