import backend
import os
import sys
import numpy as np

try:
    import onnxruntime as ort
except Exception as e:
    sys.stderr.write("Cannot import onnxruntime, maybe it's not installed.\n")


class BackendOnnxruntime(backend.Backend):

    def __init__(self):
        super(BackendOnnxruntime, self).__init__()

    def version(self):
        # paddle.version.commit
        return ort.__version__

    def name(self):
        return "onnxruntime"

    def load(self, config_arg, inputs=None, outpus=None):
        self.args = config_arg
        if os.path.exists(self.args.model_dir):
            model_file = os.path.join(self.args.model_dir, "model.onnx")
        else:
            raise ValueError(
                f"The model dir {self.args.model_dir} does not exists!")

        sess_options = ort.SessionOptions()
        if self.args.enable_mkldnn and not self.args.enable_gpu:
            self.sess = ort.InferenceSession(
                model_file, providers=['CPUExecutionProvider'])
        if self.args.enable_gpu:
            option_maps = {}
            option_maps['device_id'] = str(self.args.gpu_id)
            provider_options = [option_maps]
            if self.args.enable_trt:
                self.sess = ort.InferenceSession(
                    model_file,
                    providers=['TensorrtExecutionProvider'],
                    provider_options=provider_options)
            else:
                self.sess = ort.InferenceSession(
                    model_file,
                    providers=['CUDAExecutionProvider'],
                    provider_options=provider_options)

        return self

    def warmup(self):
        pass

    def predict(self, feed=None):
        # prepare input
        input_data = {}
        for i in range(len(self.sess.get_inputs())):
            name = self.sess.get_inputs()[i].name
            input_shape = [self.args.batch_size] + self.args.input_shape[i]
            fake_input = np.ones(input_shape, dtype=np.float32)
            input_data[name] = fake_input
        self.sess.run(None, input_data)


if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run()
    runner.report()
