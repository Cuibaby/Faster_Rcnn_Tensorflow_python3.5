#!/usr/bin/env python

# --------------------------------------------------------
# Tensorflow Faster R-CNN
# Licensed under The MIT License [see LICENSE for details]
# Written by Xinlei Chen, based on code from Ross Girshick
# --------------------------------------------------------

"""
Demo script showing detections in sample images.

See README.md for installation instructions before running.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from lib.config import config as cfg
from lib.utils.nms_wrapper import nms
from lib.utils.test import im_detect
#from nets.resnet_v1 import resnetv1
from lib.nets.vgg16 import vgg16
from lib.utils.timer import Timer

CLASSES = ('__background__',
           'aeroplane', 'bicycle', 'bird', 'boat',
           'bottle', 'bus', 'car', 'cat', 'chair',
           'cow', 'diningtable', 'dog', 'horse',
           'motorbike', 'person', 'pottedplant',
           'sheep', 'sofa', 'train', 'tvmonitor')

NETS = {'vgg16': ('vgg16_faster_rcnn_iter_70000.ckpt',), 'res101': ('res101_faster_rcnn_iter_110000.ckpt',)}
DATASETS = {'pascal_voc': ('voc_2007_trainval',), 'pascal_voc_0712': ('voc_2007_trainval+voc_2012_trainval',)}


# def vis_detections(im, class_name, dets, thresh=0.5):
#     """Draw detected bounding boxes."""
#     inds = np.where(dets[:, -1] >= thresh)[0]
#     if len(inds) == 0:
#         return
#
#     im = im[:, :, (2, 1, 0)]
#     fig, ax = plt.subplots(figsize=(12, 12))
#     ax.imshow(im, aspect='equal')
#     for i in inds:
#         bbox = dets[i, :4]
#         score = dets[i, -1]
#
#         ax.add_patch(
#             plt.Rectangle((bbox[0], bbox[1]),
#                           bbox[2] - bbox[0],
#                           bbox[3] - bbox[1], fill=False,
#                           edgecolor='red', linewidth=3.5)
#         )
#         ax.text(bbox[0], bbox[1] - 2,
#                 '{:s} {:.3f}'.format(class_name, score),
#                 bbox=dict(facecolor='blue', alpha=0.5),
#                 fontsize=14, color='white')
#
#     ax.set_title(('{} detections with '
#                   'p({} | box) >= {:.1f}').format(class_name, class_name,
#                                                   thresh),
#                  fontsize=14)
#     plt.axis('off')
#     plt.tight_layout()
#     plt.draw()

def vis_detections(im, class_name, dets, ax, thresh=0.5):
    """Draw detected bounding boxes."""
    # 选取候选框score大于阈值的dets
    inds = np.where(dets[:, -1] >= thresh)[0]
    if len(inds) == 0:
        return

    # im = im[:, :, (2, 1, 0)]
    # fig, ax = plt.subplots(figsize=(12, 12))
    # ax.imshow(im, aspect='equal')
    for i in inds:
        # 从dets中取出 bbox, score
        bbox = dets[i, :4]
        score = dets[i, -1]
        # 根据起始点坐标以及w,h 画出矩形框
        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
        )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                 fontsize=14)
    # plt.axis('off')
    # plt.tight_layout()
    # plt.draw()


def demo(sess, net, image_name):
    """Detect object classes in an image using pre-computed object proposals."""

    # Load the demo image
    im_file = os.path.join(cfg.FLAGS2["data_dir"], 'demo', image_name)
    im = cv2.imread(im_file)
    # im = cv2.imread("G:/Python Projects/py3/Faster-RCNN-TensorFlow-Python3.5-master/data/demo/000456.jpg")

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(sess, net, im)
    timer.toc()
    print('Detection took {:.3f}s for {:d} object proposals'.format(timer.total_time, boxes.shape[0]))

    # Visualize detections for each class
    # score 阈值，最后画出候选框时需要，>thresh才会被画出
    CONF_THRESH = 0.4
    # 其实是输出了很多得分高的框，只不过后续通过nms的方式将这些框进行了合并，从而达到很好的检测效果。
    # NMS_THRESH表示非极大值抑制，这个值越小表示要求的红框重叠度越小，0.0表示不允许重叠。
    NMS_THRESH = 0.1

    # python-opencv 中读取图片默认保存为[w,h,channel](w,h顺序不确定)
    # 其中 channel：BGR 存储，而画图时，需要按RGB格式，因此此处作转换。
    im = im[:, :, (2, 1, 0)]
    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(im, aspect='equal')

    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1  # because we skipped background
        cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
        # 进行非极大值抑制，得到抑制后的 dets
        keep = nms(dets, NMS_THRESH)
        dets = dets[keep, :]
        # vis_detections(im, cls, dets, thresh=CONF_THRESH)
        # 画框
        vis_detections(im, cls, dets, ax, thresh=CONF_THRESH)

    plt.axis('off')
    plt.tight_layout()
    plt.draw()


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Tensorflow Faster R-CNN demo')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16 res101]',
                        choices=NETS.keys(), default='vgg16')
    parser.add_argument('--dataset', dest='dataset', help='Trained dataset [pascal_voc pascal_voc_0712]',
                        choices=DATASETS.keys(), default='pascal_voc_0712')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    args = parse_args()

    # model path
    demonet = args.demo_net
    dataset = args.dataset
    # tfmodel = os.path.join('output', demonet, DATASETS[dataset][0], 'default', NETS[demonet][0])
    tfmodel = './default/voc_2007_trainval/default/vgg16_faster_rcnn_iter_40000.ckpt'
    """
    if not os.path.isfile(tfmodel):
        print(tfmodel)
        raise IOError(('{:s} not found.\nDid you download the proper networks from '
                       'our server and place them properly?').format(tfmodel + '.meta')
    """

    # set config
    tfconfig = tf.ConfigProto(allow_soft_placement=True)
    tfconfig.gpu_options.allow_growth = True

    # init session
    sess = tf.Session(config=tfconfig)
    # load network
    if demonet == 'vgg16':
        net = vgg16(batch_size=1)
    # elif demonet == 'res101':
        # net = resnetv1(batch_size=1, num_layers=101)
    else:
        raise NotImplementedError
    net.create_architecture(sess, "TEST", 21,
                            tag='default', anchor_scales=[8, 16, 32])
    saver = tf.train.Saver()
    saver.restore(sess, tfmodel)

    print('Loaded network {:s}'.format(tfmodel))

    # im_names = ['000456.jpg', '000457.jpg', '000542.jpg', '001150.jpg',
    #             '001763.jpg', '004545.jpg']

    # 测试图片demo的位置
    im_names = os.listdir(cfg.FLAGS2["data_dir"] + '/demo')
    for im_name in im_names:
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('Demo for data/demo/{}'.format(im_name))
        demo(sess, net, im_name)
        # 保存测试图片所在位置，并设置输出格式
        plt.savefig(cfg.FLAGS2["data_dir"] + '/test_result/' + im_name, format='png', transparent=True, pad_inches=0,
                    dpi=300, bbox_inches='tight')

    plt.show()
