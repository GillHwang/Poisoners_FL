import torch


def reverse_nn_parameters(parameters, previous_weight, args):
    """
    generate reverse all layers parameters.

    :param parameters: nn model named parameters
    :type parameters: list
    """

    args.get_logger().info("Reverse all layers of gradients from attackers")
    new_parameters = []
    for params in parameters[:len(parameters)-args.get_num_attackers]:
        new_parameters.append(params)

    for params in parameters[len(parameters)-args.get_num_attackers:]:
        for name in parameters[0].keys():
            params[name] = (2*previous_weight[name].data - params[name].data) * args.get_num_attackers()
        new_parameters.append(params)

            # new_params[name] = sum([param[name].data for param in parameters[:-(args.get_num_attackers())]])
            # new_params[name] += (2*previous_weight[name].data - parameters[-1][name].data) * args.get_num_attackers()
            # # new_params[name] += (parameters[-1][name].data) * args.get_num_attackers()
            # new_params[name] /= len(parameters)

    return new_parameters

def reverse_last_parameters(parameters, previous_weight, args):
    """
    generate reverse last layers parameters.

    :param parameters: nn model named parameters
    :type parameters: list
    """
    args.get_logger().info("Reverse last layers of gradients from attackers")
    layers = list(parameters[0].keys())
    new_parameters = []
    for params in parameters[:len(parameters)-args.get_num_attackers]:
        new_parameters.append(params)

    for params in parameters[len(parameters)-args.get_num_attackers:]:
        for name in parameters[0].keys():
            if name in layers[-(args.get_num_reverse_layers()):]:
                params[name] = (2*previous_weight[name].data - params[name].data) * args.get_num_attackers()
            else:
                params[name] = params[name]
        new_parameters.append(params)


    # for name in parameters[0].keys():
    #     if name in layers[-(args.get_num_reverse_layers()):]:
    #         new_params[name] = sum([param[name].data for param in parameters[:-(args.get_num_attackers())]])
    #         new_params[name] -= (parameters[-1][name].data) * args.get_num_attackers()
    #         new_params[name] /= (len(parameters))
    #     else:
    #         new_params[name] = sum([param[name].data for param in parameters]) / len(parameters)
    return new_parameters

def ndss_nn_parameters(parameters,args):
    """
    generate ndss parameters.

    :param parameters: nn model named parameters
    :type parameters: list
    """
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    args.get_logger().info("Averaging parameters on model ndss attackers")

    model_re = parameters[-1]
    all_updates = parameters[:-1]

    if args.get_dev_type() == 'unit_vec':
        deviation = model_re / torch.norm(model_re)
    elif args.get_dev_type() == 'sign':
        deviation = torch.sign(model_re)
    elif args.get_dev_type() == 'std':
        deviation = torch.std(all_updates, 0)

    lamda = torch.Tensor([10.0]).to(device)

    threshold_diff = 1e-5
    lamda_fail = lamda
    lamda_succ = 0

    distances = []
    for update in all_updates:
        distance = torch.norm((all_updates - update), dim=1) ** 2
        distances = distance[None, :] if not len(distances) else torch.cat((distances, distance[None, :]), 0)

    max_distance = torch.max(distances)
    del distances

    while torch.abs(lamda_succ - lamda) > threshold_diff:
        mal_update = (model_re - lamda * deviation)
        distance = torch.norm((all_updates - mal_update), dim=1) ** 2
        max_d = torch.max(distance)

        if max_d <= max_distance:
            lamda_succ = lamda
            lamda = lamda + lamda_fail / 2
        else:
            lamda = lamda - lamda_fail / 2

        lamda_fail = lamda_fail / 2

    mal_update = (model_re - lamda_succ * deviation)

    new_parameters = all_updates.extend(mal_update)

    # new_params = {}
    # for name in parameters[0].keys():
    #     new_params[name] = sum([param[name].data for param in all_updates])
    #     new_params[name] += (mal_update[name].data) * args.get_num_attackers()
    #     new_params[name] /= (len(all_updates) + args.get_num_attackers())

    return new_parameters