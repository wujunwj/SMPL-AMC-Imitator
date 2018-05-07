import matplotlib.pyplot as plt
import numpy as np
import motion_parser
import smpl_np as smpl
import copy
import transforms3d
from mpl_toolkits.mplot3d import Axes3D


def compute_rodrigues(x, y):
  theta = np.arccos(np.inner(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))
  axis = np.cross(x, y)
  return transforms3d.axangles.axangle2mat(axis, theta)


def process_femur(femur):
  child_joint = femur
  parent_joint = child_joint.parent
  smpl_direction = child_joint.coordinate - parent_joint.coordinate
  smpl_direction /= np.linalg.norm(smpl_direction)
  asf_direction = np.squeeze(np.array(child_joint.direction))
  child_joint.default_R = compute_rodrigues(smpl_direction, asf_direction)


def set_to_smpl(joints, smpl_J):
  semantic = motion_parser.joint_semantic()
  for k, v in semantic.items():
    joints[v].coordinate = smpl_J[k] / 0.45 * 10


def compute_default_R(joints):
  '''Actually we only consider legs'''
  R = np.broadcast_to(np.expand_dims(np.eye(3), axis=0), (24, 3, 3))
  _, _, J = smpl.smpl_model('./model.pkl', R)

  set_to_smpl(joints, J)

  process_femur(joints['lfemur'])
  process_femur(joints['rfemur'])


def draw_body(joints):
  fig = plt.figure()
  ax = Axes3D(fig)

  # ax.set_xlim3d(-30, 50)
  # ax.set_ylim3d(0, 30)
  # ax.set_zlim3d(0, 30)

  ax.set_xlim3d(-20, 40)
  ax.set_ylim3d(-30, 30)
  ax.set_zlim3d(-40, 20)

  xs, ys, zs = [], [], []
  for joint in joints.values():
    if joint.coordinate is None:
      continue
    xs.append(joint.coordinate[0])
    ys.append(joint.coordinate[1])
    zs.append(joint.coordinate[2])
  plt.plot(zs, xs, ys, 'b.')

  for joint in joints.values():
    if joint.coordinate is None:
      continue
    child = joint
    if child.parent is not None:
      parent = child.parent
      xs = [child.coordinate[0], parent.coordinate[0]]
      ys = [child.coordinate[1], parent.coordinate[1]]
      zs = [child.coordinate[2], parent.coordinate[2]]
      plt.plot(zs, xs, ys, 'r')
  plt.show()


def obj_save(path, vertices, faces=None):
  with open(path, 'w') as fp:
    for v in vertices:
      fp.write('v %f %f %f\n' % (v[0], v[1], v[2]))
    if faces is not None:
      for f in faces + 1:
        fp.write('f %d %d %d\n' % (f[0], f[1], f[2]))


if __name__ == '__main__':
  joints = motion_parser.parse_asf('./data/01/01.asf')
  compute_default_R(joints)

  motions = motion_parser.parse_amc('./data/nopose.amc')
  # motions = motion_parser.parse_amc('./data/01/01_01.amc')
  # joints['root'].set_motion(motions[0], direction=np.array([-1, -1, -1]))
  joints['root'].set_motion(motions[0])

  semantic = motion_parser.joint_semantic()
  jindex = motion_parser.joint_index()

  R = np.broadcast_to(np.expand_dims(np.eye(3), axis=0), (24, 3, 3))
  _, _, J = smpl.smpl_model('./model.pkl', R)
  J += np.array([0, 0, 1.5])
  joints_new = motion_parser.parse_asf('./data/01/01.asf')
  set_to_smpl(joints_new, J)

  for k, v in joints_new.items():
    joints[k + '_'] = v

  draw_body(joints)

  R = np.empty([24, 3, 3])
  for i in range(24):
    R[i] = np.eye(3)
  for k, v in semantic.items():
    if joints[v].parent is not None:
      idx = jindex[joints[v].parent.name]
      R[idx] = joints[v].default_R

  # for k, v in semantic.items():
  #   R[k] = np.dot(R[k], np.array(joints[v].matrix))
  #   if joints[v].parent is not None:
  #     R[k] = np.dot(R[k], np.array(np.linalg.inv(joints[v].parent.matrix)))

  verts, faces, J = smpl.smpl_model('./model.pkl', R)
  obj_save('./smpl.obj', verts, faces)

