#!/usr/bin/env python
import os
import sys
import argparse
import tensorflow.compat.v1 as tf

from .model import OpenNsfwModel, InputType
from .image_utils import create_tensorflow_image_loader
from .image_utils import create_yahoo_image_loader

import numpy as np


IMAGE_LOADER_TENSORFLOW = "tensorflow"
IMAGE_LOADER_YAHOO = "yahoo"


class YahooNsfwClassify:
    def __init__(self) -> None:
        tf.disable_v2_behavior()
        self.model = OpenNsfwModel()
        self.sess = tf.Session()
        input_type = InputType[InputType.TENSOR.name]
        self.model.build(weights_path=self._get_weights_path, input_type=input_type)
        self.fn_load_image = create_yahoo_image_loader()
        self.sess.run(tf.global_variables_initializer())

    @property
    def _get_weights_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            'model_file/open_nsfw-weights.npy'
        )

    def yahoo_nsfw_classify(self, input_file):
        image = self.fn_load_image(input_file)
        predictions = self.sess.run(self.model.predictions, feed_dict={self.model.input: image})
        return (predictions[0][1], round(predictions[0][1]*100, 2))


def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", help="Path to the input image.\
                        Only jpeg images are supported.")

    parser.add_argument("-m", "--model_weights", required=True,
                        help="Path to trained model weights file")

    parser.add_argument("-l", "--image_loader",
                        default=IMAGE_LOADER_YAHOO,
                        help="image loading mechanism",
                        choices=[IMAGE_LOADER_YAHOO, IMAGE_LOADER_TENSORFLOW])

    parser.add_argument("-i", "--input_type",
                        default=InputType.TENSOR.name.lower(),
                        help="input type",
                        choices=[InputType.TENSOR.name.lower(),
                                 InputType.BASE64_JPEG.name.lower()])

    args = parser.parse_args()

    model = OpenNsfwModel()

    with tf.Session() as sess:

        input_type = InputType[args.input_type.upper()]
        model.build(weights_path=args.model_weights, input_type=input_type)

        fn_load_image = None

        if input_type == InputType.TENSOR:
            if args.image_loader == IMAGE_LOADER_TENSORFLOW:
                fn_load_image = create_tensorflow_image_loader(tf.Session(graph=tf.Graph()))
            else:
                fn_load_image = create_yahoo_image_loader()
        elif input_type == InputType.BASE64_JPEG:
            import base64
            def fn_load_image(filename): return np.array([base64.urlsafe_b64encode(open(filename, "rb").read())])

        sess.run(tf.global_variables_initializer())

        image = fn_load_image(args.input_file)

        predictions = \
            sess.run(model.predictions,
                     feed_dict={model.input: image})

        print("Results for '{}'".format(args.input_file))
        print("\tSFW score:\t{}\n\tNSFW score:\t{}".format(*predictions[0]))


if __name__ == "__main__":
    main(sys.argv)
