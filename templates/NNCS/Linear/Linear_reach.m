function [R, reachTime] = Linear_reach(NN_path,dynamics_func,dim,nI,Ts,outputMat,feedbackMap,lb,ub,num_of_steps,reachMethod,lb_ref,ub_ref)
    %% Create the NNV class (NNCS class)
    % Load controller
    controller = Load_nn(NN_path); % User specifies 
    % Load plant (method 1)
    plant = DNonLinearODE(dim,nI,dynamics_func,Ts,outputMat); % User specifies all matrices and time step (Ts)
    % Contruct NNCS objLct
    nncs = DNonlinearNNCS(controller,plant,feedbackMap);
    
    %% Reachability
    reachPRM.init_set = Star(lb,ub); % User specifies lower and upper bounds vectors
    reachPRM.numSteps = num_of_steps; % User specifies number of steps
    reachPRM.reachMethod = reachMethod; % Only allow approximate methods (set as fixed)
    reachPRM.numCores = 1; % User specifies number of cores (1 as default)
    if isempty(lb)
        reachPRM.ref_input = [];
    else
        reachPRM.ref_input = Star(lb_ref,ub_ref);% User specifies reference input ([] as default (empty = no reference inputs needed))
    end
    [R,reachTime] = nncs.reach(reachPRM); % Execute reachability analysis
    
    end


    %% [r,rt] = Linear_reach('controller_test.mat',@test_dynamicsD,6,1,0.2,[0 0 0 0 1 0;1 0 0 -1 0 0; 0 1 0 0 -1 0],[0],[90;29;0;30;30;0], [92;30;0;31;30.2;0], 5, 'approx-star',[30;1.4],[30;1.4]);