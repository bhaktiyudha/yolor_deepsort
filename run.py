import sys
sys.path.insert(0, './yolor')

from yolor.utils.google_utils import attempt_download
from yolor.models.experimental import attempt_load
from yolor.utils.datasets import LoadImages, LoadStreams
from yolor.utils.general import check_img_size, non_max_suppression, scale_coords, xyxy2xywh
from yolor.utils.torch_utils import select_device, time_synchronized
from yolor.utils.plots import plot_one_box
from yolor.models.models import *
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort
import argparse
import os
import platform
import shutil
import time
from pathlib import Path
import cv2
import torch
import torch.backends.cudnn as cudnn
font_thickness = 1
font_size = 0.5
font_color = (0, 0, 255)
middle_line_position = 500   
up_line_position = middle_line_position - 15
down_line_position = middle_line_position + 15
# List for store vehicle count information
temp_up_list = []
temp_down_list = []
up_list = [0, 0, 0, 0,0,0,0,0]
down_list = [0, 0, 0, 0,0,0,0,0]

def find_center(x, y, w, h):
    x1=int(w/2)
    y1=int(h/2)
    cx = x+x1
    cy=y+y1
    return cx, cy

def load_classes(path):
    # Loads *.names file at 'path'
    with open(path, 'r') as f:
        names = f.read().split('\n')
    return list(filter(None, names)) 

def compute_color_for_id(label):
    """
    Simple function that adds fixed color depending on the id
    """
    palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)

    color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def detect(opt):
    out, source, yolo_cfg,yolo_weights, deep_sort_weights, show_vid, save_vid, save_txt, imgsz, evaluate,names = \
        opt.output, opt.source, opt.yolo_cfg, opt.yolo_weights, opt.deep_sort_weights, opt.show_vid, opt.save_vid, \
            opt.save_txt, opt.img_size, opt.evaluate, opt.names
    webcam = source == '0' or source.startswith(
        'rtsp') or source.startswith('http') or source.endswith('.txt')

    # initialize deepsort
    cfg = get_config()
    cfg.merge_from_file(opt.config_deepsort)
    attempt_download(deep_sort_weights)
    deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                        max_dist=cfg.DEEPSORT.MAX_DIST, min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                        nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                        max_age=cfg.DEEPSORT.MAX_AGE, n_init=cfg.DEEPSORT.N_INIT, nn_budget=cfg.DEEPSORT.NN_BUDGET,
                        use_cuda=True)

    # Initialize
    device = select_device(opt.device)

    # The MOT16 evaluation runs multiple inference streams in parallel, each one writing to
    # its own .txt file. Hence, in that case, the output folder is not restored
    if not evaluate:
        if os.path.exists(out):
            pass
            shutil.rmtree(out)  # delete output folder
        os.makedirs(out)  # make new output folder
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    # model = attempt_load(yolo_weights, map_location=device)  # load FP32 model
    model = Darknet(yolo_cfg, imgsz).cuda()
    model.load_state_dict(torch.load(yolo_weights, map_location=device)['model'])
    # stride = int(model.stride.max())  # model stride
    # imgsz = check_img_size(imgsz, s=stride)  # check img_size
    # names = model.module.names if hasattr(model, 'module') else model.names  # get class names
    model.to(device).eval()
    if half:
        model.half()  # to FP16

    # Set Dataloader
    vid_path, vid_writer = None, None
    # Check if environment supports image displays
    # if show_vid:
    #     show_vid = check_imshow()

    if webcam:
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz)
    else:
        dataset = LoadImages(source, img_size=imgsz)

    # Get names and colors
    names = load_classes(names)
    color = [[random.randint(0, 255) for _ in range(3)] for _ in range(len(names))]

    # Run inference
    t0 = time.time()
    img = torch.zeros((1, 3, imgsz, imgsz), device=device)  # init img
    _ = model(img.half() if half else img) if device.type != 'cpu' else None  # run once

    save_path = str(Path(out))
    # extract what is in between the last '/' and last '.'
    txt_file_name = source.split('/')[-1].split('.')[0]
    txt_path = str(Path(out)) + '/' + txt_file_name + '.txt'

    for frame_idx, (path, img, im0s, vid_cap) in enumerate(dataset):
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]

        # Apply NMS
        pred = non_max_suppression(
            pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if webcam:  # batch_size >= 1
                p, s, im0 = path[i], '%g: ' % i, im0s[i].copy()
            else:
                p, s, im0 = path, '', im0s

            s += '%gx%g ' % img.shape[2:]  # print string
            save_path = str(Path(out) / Path(p).name)

            if det is not None and len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += '%g %ss, ' % (n, names[int(c)])  # add to string

                xywhs = xyxy2xywh(det[:, 0:4])
                confs = det[:, 4]
                clss = det[:, 5]

                # pass detections to deepsort
                outputs = deepsort.update(xywhs.cpu(), confs.cpu(), clss, im0)
                
                # draw boxes for visualization
                if len(outputs) > 0:
                    for j, (output, conf) in enumerate(zip(outputs, confs)): 
                        
                        bboxes = output[0:4]
                        id = output[4]
                        cls = output[5]

                        c = int(cls)  # integer class
                        label = f'{id} {names[c]} {conf:.2f}'
                        color = compute_color_for_id(id)
                        plot_one_box(bboxes, im0, label=label, color=color, line_thickness=1)

                        ix = int((bboxes[0]+bboxes[2])/2) 
                        iy = int((bboxes[1]+bboxes[3])/2)
                        
                        # # Find the current position of the vehicle
                        if (iy > up_line_position) and (iy < middle_line_position):

                            if id not in temp_up_list:
                                temp_up_list.append(id)

                        elif iy < down_line_position and iy > middle_line_position:
                            if id not in temp_down_list:
                                temp_down_list.append(id)
                                
                        elif iy < up_line_position:
                            if id in temp_down_list:
                                temp_down_list.remove(id)
                                up_list[c] = up_list[c]+1

                        elif iy > down_line_position:
                            if id in temp_up_list:
                                temp_up_list.remove(id)
                                down_list[c] = down_list[c] + 1
                        # Draw circle in the middle of the rectangle
                        cv2.circle(im0,(ix,iy), 2, (0, 0, 255), -1)  # end here
                        
                        # print FPS
                        #cv2.putText(im0, "FPS="+str(int(1/(t2-t1))), (0,25), cv2.FONT_HERSHEY_COMPLEX, 1, (0,0,255), 2)

                        if save_txt:
                            # to MOT format
                            bbox_top = output[0]
                            bbox_left = output[1]
                            bbox_w = output[2] - output[0]
                            bbox_h = output[3] - output[1]
                            # Write MOT compliant results to file
                            with open(txt_path, 'a') as f:
                               f.write(('%g ' * 10 + '\n') % (frame_idx, id, bbox_top,
                                                           bbox_left, bbox_w, bbox_h, -1, -1, -1, -1))  # label format

            #else:
            #    deepsort.increment_ages()

            # Print time (inference + NMS)
            print('%sDone. (%.3fs)' % (s, t2 - t1))

            # Stream results
            if show_vid:
                cv2.imshow(p, im0)
                if cv2.waitKey(1) == ord('q'):  # q to quit
                    raise StopIteration
            # ih, iw, channels = img.shape
            cv2.line(im0, (0, middle_line_position), (1280, middle_line_position), (255, 0, 255), 2)
            cv2.line(im0, (0, up_line_position), (1280, up_line_position), (0, 0, 255), 2)
            cv2.line(im0, (0, down_line_position), (1280, down_line_position), (0, 0, 255), 2)

            # Draw counting texts in the frame
            cv2.putText(im0, "Up", (110, 40), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)
            cv2.putText(im0, "Down", (160, 40), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)
            cv2.putText(im0, "Car:        "+str(up_list[2])+"     "+ str(down_list[2]), (20, 60), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)
            cv2.putText(im0, "Motorbike:  "+str(up_list[1])+"     "+ str(down_list[1]), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)
            cv2.putText(im0, "Bus:        "+str(up_list[5])+"     "+ str(down_list[5]), (20, 100), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)
            cv2.putText(im0, "Truck:      "+str(up_list[7])+"     "+ str(down_list[7]), (20, 120), cv2.FONT_HERSHEY_SIMPLEX, font_size, font_color, font_thickness)


            # Save results (image with detections)
            if save_vid:
                if vid_path != save_path:  # new video
                    print("save=", save_path)
                    vid_path = save_path
                    if isinstance(vid_writer, cv2.VideoWriter):
                        vid_writer.release()  # release previous video writer
                    if vid_cap:  # video
                        fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    else:  # stream
                        fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path += '.mp4'

                    vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                vid_writer.write(im0)

    if save_txt or save_vid:
        print('Results saved to %s' % os.getcwd() + os.sep + out)
        if platform == 'darwin':  # MacOS
            os.system('open ' + save_path)

    print('Done. (%.3fs)' % (time.time() - t0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--yolo_weights', type=str, default='yolor/weights/yolor-p6.pt', help='model.pt path')
    parser.add_argument('--yolo_cfg', type=str, default='yolor/cfg/yolor_p6.cfg', help='*.cfg path')
    parser.add_argument('--deep_sort_weights', type=str, default='deep_sort_pytorch/deep_sort/deep/checkpoint/ckpt.t7', help='ckpt.t7 path')
    # file/folder, 0 for webcam
    parser.add_argument('--source', type=str, default='0', help='source')
    parser.add_argument('--output', type=str, default='inference/output', help='output folder')  # output folder
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.4, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.5, help='IOU threshold for NMS')
    parser.add_argument('--fourcc', type=str, default='mp4v', help='output video codec (verify ffmpeg support)')
    parser.add_argument('--device', default='0', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--show-vid', action='store_true', help='display tracking video results')
    parser.add_argument('--save-vid', action='store_true', help='save video tracking results')
    parser.add_argument('--save-txt', action='store_true', help='save MOT compliant results to *.txt')
    # class 0 is person, 1 is bycicle, 2 is car... 79 is oven
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 16 17')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--evaluate', action='store_true', help='augmented inference')
    parser.add_argument('--config_deepsort', type=str, default='deep_sort_pytorch/configs/deep_sort.yaml')
    parser.add_argument('--names', type=str, default='yolor/data/coco.names', help='*.cfg path')
    args = parser.parse_args()
    args.img_size = check_img_size(args.img_size)

    with torch.no_grad():
        detect(args)
