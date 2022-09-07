import cv2

# import numpy as np


def main():
    cap = cv2.VideoCapture(0)

    # Define the codec and create VideoWriter object
    # fourcc = cv2.VideoWriter_fourcc(*'XVID')   DOESN'T WORK
    fourcc = cv2.cv.CV_FOURCC(*"XVID")
    out = cv2.VideoWriter("output.avi", fourcc, 20.0, (640, 480))

    while cap.isOpened():
        ret, frame = cap.read()
        if ret is True:
            frame = cv2.flip(frame, 0)

            # write the flipped frame
            out.write(frame)

            # cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            break

    # Release everything if job is finished
    cap.release()
    out.release()
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
