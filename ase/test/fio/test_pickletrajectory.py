import pytest
import numpy as np
import sys
from subprocess import check_call, check_output

from pathlib import Path

from ase.build import bulk
from ase.io import read, write
from ase.io.pickletrajectory import PickleTrajectory
from ase.calculators.calculator import compare_atoms
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from ase.io.bundletrajectory import print_bundletrajectory_info


trajname = 'pickletraj.traj'


def test_raises():
    with pytest.raises(DeprecationWarning):
        PickleTrajectory(trajname, 'w')


@pytest.fixture
def images():
    atoms = bulk('Ti') * (1, 2, 1)
    atoms.symbols = 'Au'
    atoms.calc = EMT()
    atoms1 = atoms.copy()
    atoms1.rattle()
    images = [atoms, atoms1]

    # Set all sorts of weird data:
    for i, atoms in enumerate(images):
        ints = np.arange(len(atoms)) + i
        floats = 1.0 + np.arange(len(atoms))
        atoms.set_tags(ints)
        atoms.set_initial_magnetic_moments(floats)
        atoms.set_initial_charges(floats)
        atoms.set_masses(floats)
        floats3d = 1.2 * np.arange(3 * len(atoms)).reshape(-1, 3)
        atoms.set_momenta(floats3d)
        atoms.info = {'hello': 'world'}
        atoms.calc = EMT()
        atoms.get_potential_energy()

    atoms.set_constraint(FixAtoms(indices=[0]))
    return [atoms, atoms1]


def read_images(filename):
    with PickleTrajectory(filename, _warn=False) as traj:
        return list(traj)


@pytest.fixture
def trajfile(images):
    ptraj = PickleTrajectory(trajname, 'w', _warn=False)
    for image in images:
        ptraj.write(image)
    ptraj.close()
    return trajname


def images_equal(images1, images2):
    if len(images1) != len(images2):
        return False

    for atoms1, atoms2 in zip(images1, images2):
        if len(compare_atoms(atoms1, atoms2)) > 0:
            return False

    return True


def test_write_read(images, trajfile):
    images1 = read_images(trajfile)
    assert images_equal(images, images1)


def test_append(images, trajfile):
    with PickleTrajectory(trajfile, 'a', _warn=False) as traj:
        for image in images:
            traj.write(image)

    images1 = read_images(trajfile)
    assert images_equal(images * 2, images1)


def test_old_trajectory_conversion_utility(images, trajfile):
    trajpath = Path(trajfile)
    assert trajpath.exists()
    check_call([sys.executable, '-m', 'ase.io.trajectory', trajfile])
    oldtrajpath = trajpath.with_suffix('.traj.old')
    assert oldtrajpath.exists()
    assert trajpath.exists()  # New file should be where the old one was
    new_images = read(trajpath, ':', format='traj')
    assert images_equal(images, new_images)


@pytest.fixture
def bundletraj(images):
    fname = 'traj.bundle'
    write(fname, images, format='bundletrajectory')
    return fname


def test_bundletrajectory_info(images, bundletraj, capsys):
    print_bundletrajectory_info(bundletraj)
    output, _ = capsys.readouterr()

    natoms = len(images[0])
    expected_substring = f'Number of atoms: {natoms}'
    assert expected_substring in output

    # Same thing but via main():
    output2 = check_output([sys.executable,
                            '-m', 'ase.io.bundletrajectory', bundletraj],
                           encoding='ascii')
    assert expected_substring in output2
