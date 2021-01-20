"""
File modify from https://github.com/open-mmlab/mmcv
License File Available at:
https://github.com/open-mmlab/mmcv/blob/master/LICENSE
"""
import os
import os.path as osp

from .hooks.base_hook import HOOKS
from .log_meter import LossMeter
from .priority import get_priority
from pytorch_trainer.utils import Registry

TRAINER = Registry('trainer')


class BaseTrainer():
    """The base class of Trainer, a training helper for PyTorch.
    All subclasses should implement the following APIs:
    - ``run()``
    - ``train()``
    - ``val()``
    - ``save_checkpoint()``
    Args:
        model (:obj:`torch.nn.Module`): The model to be run.
        optimizer (dict or :obj:`torch.optim.Optimizer`): It can be either an
            optimizer (in most cases) or a dict of optimizers (in models that
            requires more than one optimizer, e.g., GAN).
        work_dir (str, optional): The working directory to save checkpoints
            and logs. Defaults to None.
        logger (:obj:`logging.Logger`): Logger used during training.
             Defaults to None. (The default value is just for backward
             compatibility)
        meta (dict | None): A dict records some import information such as
            environment info and seed, which will be logged in logger hook.
            Defaults to None.
        max_epochs (int, optional): Total training epochs.
    """

    def __init__(self,
                 model,
                 optimizer=None,
                 work_dir=None,
                 logger=None,
                 meta=None,
                 max_epoch=None):

        # TODO: checker
        # # check the type of `optimizer`
        # if not isinstance(optimizer, Optimizer) and optimizer is not None:
        #     raise TypeError(
        #         f'optimizer must be a torch.optim.Optimizer object'
        #         f'or dict or None, but got {type(optimizer)}')

        # # check the type of `logger`
        # if not isinstance(logger, logging.Logger):
        #     raise TypeError(f'logger must be a logging.Logger object, '
        #                     f'but got {type(logger)}')

        # # check the type of `meta`
        # if meta is not None and not isinstance(meta, dict):
        #     raise TypeError(
        #         f'meta must be a dict or None, but got {type(meta)}')

        self.model = model
        self.optimizer = optimizer
        self.logger = logger
        self.meta = meta  # TODO: discuss meta format

        # create work_dir
        if isinstance(work_dir, str):
            self.work_dir = osp.abspath(work_dir)
            if not osp.isdir(work_dir):
                os.makedirs(work_dir)
        elif work_dir is None:
            self.work_dir = None
        else:
            raise TypeError('Argument "work_dir" must be a str or None')

        # get model name from the model class
        if hasattr(self.model, 'module'):
            self._model_name = self.model.module.__class__.__name__
        else:
            self._model_name = self.model.__class__.__name__

        self.mode = None
        self._hooks = []
        self._epoch = 0
        self._inner_iter = 0
        self._max_epoch = max_epoch
        self.loss_meters = LossMeter()

    @property
    def epoch(self):
        return self._epoch

    @property
    def max_epochs(self):
        return self._max_epochs

    def call_hook(self, fn_name):
        """Call all hooks by name.
        Args:
            fn_name (str): The function name in each hook to be called, such as
                "before_train_epoch".
        """
        for hook in self._hooks:
            getattr(hook, fn_name)(self)

    def register_hook(self, hook, priority='NORMAL'):
        """Register a hook into the hook list.
        The hook will be inserted into a priority queue, with the specified
        priority (See :class:`Priority` for details of priorities).
        For hooks with the same priority, they will be triggered in the same
        order as they are registered.
        Args:
            hook (:obj:`Hook`): The hook to be registered.
            priority (int or str or :obj:`Priority`): Hook priority.
                Lower value means higher priority.

        """
        # assert isinstance(hook(), Hook)
        if hasattr(hook, 'priority'):
            raise ValueError('"priority" is a reserved attribute for hooks')

        hook.priority = get_priority(priority)
        # insert the hook to a sorted list
        for i in range(len(self._hooks) - 1, -1, -1):
            if hook.priority >= self._hooks[i].priority:
                self._hooks.insert(i + 1, hook)
                return
        self._hooks.insert(0, hook)

    def register_optimizer_hook(self, optimizer_config):
        """mandatory hook"""
        # TODO: builder and assign configure
        optimizer_hook = HOOKS.get('OptimizerHook')()
        self.register_hook(optimizer_hook, priority='High')

    def register_scheduler(self, scheduler_config=None):
        """optional hook"""
        if scheduler_config is None:
            return
        # TODO: builder and assign configure
        scheduler_hook = HOOKS.get('SchedulerHook')()
        self.register_hook(scheduler_hook)

    def register_checkpoint_hook(self, checkpoint_config=None):
        """optional hook"""
        if checkpoint_config is None:
            return
        # TODO: builder  and assign configure
        checkpoint_hook = HOOKS.get('CheckpointHook')()
        self.register_hook(checkpoint_hook)

    def register_logger_hooks(self, log_config=None):
        """optional hook"""
        if log_config is None:
            return
        # # TODO: builder  and assign configure
        # for config in log_config:
        for hook_name in ['LossLoggerHook', 'TensorboardLoggerHook', 'TextLoggerHook']:
            log_hook = HOOKS.get(hook_name)()
            self.register_hook(log_hook, priority='VERY_LOW')

    def register_training_hooks(self,
                                config):
        """Register hooks for training.
            append hook into list self.hooks
        """
        self.register_optimizer_hook(config.optimizer_config)
        self.register_scheduler(config.scheduler_config)
        self.register_checkpoint_hook(config.checkpoint_config)
        self.register_logger_hooks(config.log_config)