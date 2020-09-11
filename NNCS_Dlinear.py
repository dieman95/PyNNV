import json
import matlab
import matlab.engine
from pathlib import Path

import numpy as np
def array2str(arr, precision=None):
    s=np.array_str(arr, precision=precision)
    return s.replace('\n', ',')

import re
import ast
import numpy as np
def str2array(s):
    # Remove space after [
    s=re.sub('\[ +', '[', s.strip())
    # Replace commas and spaces
    s=re.sub('[,\s]+', ', ', s)
    return np.array(ast.literal_eval(s)).tolist()




class NNCS_Dlinear:
    def __init__(self,eng=None):
        self.A =  []
        self.B = []
        self.C=  []
        self.D = []
        self.Ts = None # Integer
        self.nnfile = "" #Path of the NN file
        # Following are needed for reachability and Verification
        self.lb = []
        self.ub = []
        self.method = []
        self.cores = 1
        self.steps = 0
        self.lbRefInput = []
        self.ubRefInput = []

        # Following is needed for verification...
        self.HalfSpaceMatrix = []  # // any matrix (G)
        self.HalfSpaceVector = []  # // any matrix (g)
        self.eng = eng
        self.verify = False
        self.reach = False

    def setPlant(self,A,B,C,D,Ts):
        self.A =  A
        self.B = B
        self.C=  C #[]
        self.D = D
        
        self.Ts = Ts #None # Integer


    def setController(self,nnfile):
        self.nnfile = nnfile #Path of the NN file

    def getController(self):
        # controller = Load_nn('NN-path'); % User specifies 
        return self.eng.Load_nn(self.nnfile)

    def getPlant(self):
        return self.eng.DLinearODE(self,self.A,self.B,self.C,self.D,self.Ts)

    def getNNCS(self):
        return self.eng.DLinearNNCS(self.getController(),self.getPlant());


    def str2matlabArray(self,strmat):
        return self.eng.str2num(strmat)


    def setReachParam(self,init_set,numSteps,reachMethod,numCores,refInput, halfSpaceMatrix=None, halfSpaceVector=None):
        self.init_set = init_set
        self.steps = numSteps
        self.reach_method = reachMethod
        self.cores = numCores
        self.refInput = refInput
        self.HalfSpaceMatrix = halfSpaceMatrix
        self.HalfSpaceVector = halfSpaceVector


    def parseReachParam(self,lb, ub, numSteps, reachMethod, numCores, lbRef, ubRef,halfSpaceMatrix,halfSpaceVector,doReachability,doVerify):
        initSet = None
        refInput = None
        self.lb = lb
        self.ub= ub
        self.steps = numSteps
        self.reach_method = reachMethod
        self.cores = numCores
        self.lbRefInput = lbRef
        self.ubRefInput = ubRef
        self.HalfSpaceMatrix = halfSpaceMatrix
        self.HalfSpaceVector = halfSpaceVector
        
        self.reach = doReachability
        self.verify = doVerify
        # initSet = self.eng.Star(lb,ub)
        # self.refInput = self.eng.Star(lbRef,ubRef)
        # print(initSet)
        # print(refInput)
        
        # self.setReachParam(initSet,numSteps,reachMethod,numCores,refInput,halfSpaceMatrix,halfSpaceVector)    

    def printDebug(self):
        print(self.lb,self.ub)
        print(self.steps)
        print(self.nnfile)
        # print("RefInput")
        # print(self.refInput)
        

    def parseJson(self,jsonfile):
        print("parsing file:",jsonfile)
        data = None
        with open(jsonfile) as f:
            data = json.load(f)

        newdata ={}
        
        newdata['A'] = self.str2matlabArray(data['A'])
        newdata['B'] = self.str2matlabArray(data['B'])
        newdata['C'] = self.str2matlabArray(data['C'])
        newdata['D'] = self.str2matlabArray(data['D'])
        newdata['Ts'] = data['Ts']
        
        
        newdata['lb'] = self.str2matlabArray(data['lb'])
        
        newdata['ub'] = self.str2matlabArray(data['ub'])
        newdata['lb-refInput'] = self.str2matlabArray(data['lb-refInput'])
        newdata['ub-refInput'] = self.str2matlabArray(data['ub-refInput'])
        newdata['HalfSpace-matrix'] =self.str2matlabArray(data['HalfSpace-matrix'])
        newdata['HalfSpace-vector'] =self.str2matlabArray(data['HalfSpace-vector'])

        if data['reach']==1:
            newdata['reach'] = True
        else:
            newdata['reach']= False

        if data['verify']==1:
            newdata['verify'] = True
        else:
            newdata['verify']= False


        self.setPlant(newdata['A'],newdata['B'], newdata['C'],newdata['D'],newdata['Ts'])
        self.setController(data['nnfile'])
        self.parseReachParam(lb=newdata['lb'],ub=newdata['ub'], numSteps=data['steps'],reachMethod=data['reach-method'],
                            numCores=data['cores'],lbRef=newdata['lb-refInput'],ubRef=newdata['ub-refInput'], halfSpaceMatrix= newdata['HalfSpace-matrix'], halfSpaceVector= newdata['HalfSpace-vector'] ,doReachability=newdata['reach'],doVerify=newdata['verify'])

    def execute(self):
        self.getNNCS()
    
    def invokeReachibility(self):
        return self.eng.DLinearNNCS_reach(self.nnfile,self.A,self.B,self.C,self.D,self.Ts,self.lb,self.ub,self.steps,self.reach_method,self.cores,self.lbRefInput,self.ubRefInput)

    def invokeVerifier(self):
        return self.eng.DLinearNNCS_verify(self.nnfile,self.A,self.B,self.C,self.D,self.Ts,self.lb,self.ub,self.steps,self.reach_method,self.cores,self.lbRefInput,self.ubRefInput,self.HalfSpaceMatrix,self.HalfSpaceVector)
    
    def doVerify(self):
        return self.verify

    def doReach(self):
        return self.reach    

    
    def compute(self):
        result = {}
        if self.doReach():
            result['reachability'] = self.invokeReachibility()

        if self.doVerify():
            result['verification'] = self.invokeVerifier()
        return result

def main():
        

    # START MATLAB ENGINE
    # eng = matlab.engine.start_matlab()
    eng = matlab.engine.start_matlab('-nojvm')


    # ADD PATHS OF NEEDED FUNCTIONS TO MATLAB ENVIRONMENT
    matlab_function_path_list = []
    local_matlab_function_path = str(Path(Path(__file__).absolute().parent, "templates/CNN/Brightening"))
    matlab_function_path_list.append(local_matlab_function_path)
    local_matlab_function_path = str(Path(Path(__file__).absolute().parent, "templates/CNN/Darkening"))
    matlab_function_path_list.append(local_matlab_function_path)
    local_matlab_function_path = str(Path(Path(__file__).absolute().parent, "templates/CNN/RandomNoise"))
    matlab_function_path_list.append(local_matlab_function_path)

    # image_path = str(Path(Path(__file__).absolute().parent, "templates/CNN/image40.png"))

    #
    # EXECUTE MATLAB ENGINE
    #
    # eng.addpath(*matlab_function_path_list)
    eng.addpath(eng.genpath('/home/ubuntu/yogesh/aatools/diego-nnv/nnv/code/nnv'))
    
    meanV, stdV, reach_method  = (matlab.double([0.4914, 0.4822, 0.4465]) , matlab.double([0.2023, 0.1994, 0.2010]) , 'approx-star')
    # eng.cd(str(Path(Path(__file__).absolute().parent, "templates/CNN/Brightening")),nargout=0)
    image_path = str(Path(Path(__file__).absolute().parent, "templates","CNN", 'image40.png').absolute())
    # print(mat_file)
    print(image_path)
    network_directory_path = Path(Path(__file__).absolute().parent, "templates","CNN")
    mat_file_list = sorted(network_directory_path.glob("*.mat"))
    print(mat_file_list)

    if len(mat_file_list) == 0:
        raise RuntimeError(
        "lec directory \"{0}\" must contain at least one mat-file"
        " (that contains a neural network).".format(network_directory_path))
    mat_file = mat_file_list[0].absolute()
    pixels =100

    
    eng.cd(str(Path(Path(__file__).absolute().parent, "templates/NNCS/DLinear")),nargout=0)
    jsonfile = Path(Path(__file__).absolute().parent, "templates","NNCS","DLinear",'inputJson.json')
    # print(jsonfile)
    simObj = NNCS_Dlinear(eng)
    simObj.parseJson(str(jsonfile))
    print(simObj.compute())
    # simObj.invokeReachibility()
    # # simObj.printDebug()
    # simObj.invokeVerifier()

    # if simObj.doReach():
    #     result = simObj.invokeReachibility()

    # if simObj.doVerify():
    #     result = simObj.invokeVerifier()

        # simObj.execute()
    # except Exception as e:
    #     print(e)    
    # finally:
    #     print("Finally..")    
    #     eng.exit()
    eng.exit()

if __name__ == "__main__":
    main()


# A = [0 1 0 0 0 0 0; 0 0 1 0 0 0 0; 0 0 0 0 0 0 1; 0 0 0 0 1 0 0; 0 0 0 0 0 1 0; 0 0 0 0 0 -2 0; 0 0 -2 0 0 0 0];
# B = [0; 0; 0; 0; 0; 2; 0];
# C = [1 0 0 -1 0 0 0; 0 1 0 0 -1 0 0; 0 0 0 0 1 0 0];  % feedback relative distance, relative velocity, longitudinal velocity
# D = [0; 0; 0];
# NN_Path = 'controller.mat';
# lb = [90;29;0;30;30;0;-10];
# ub = [92;30;0;31;30.2;0;-10];
# G = [1 0 0 -1 -1.4 0 0];
# g = 10;
# DLinearNNCS_verify(NN_Path,A,B,C,D,0.2,lb,ub,5,'approx-star',1,[30;1.4],G,g)    
