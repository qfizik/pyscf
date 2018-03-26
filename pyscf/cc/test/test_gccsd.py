#!/usr/bin/env python
# Copyright 2014-2018 The PySCF Developers. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import numpy
from pyscf import lib
from pyscf import scf
from pyscf import gto
from pyscf import cc
from pyscf import ao2mo
from pyscf.cc import gccsd
from pyscf.cc import gccsd_rdm
from pyscf.cc import ccsd
from pyscf.cc import uccsd

mol = gto.Mole()
mol.atom = [
    [8 , (0. , 0.     , 0.)],
    [1 , (0. , -0.757 , 0.587)],
    [1 , (0. , 0.757  , 0.587)]]
mol.verbose = 5
mol.output = '/dev/null'
mol.basis = 'cc-pvdz'
mol.spin = 2
mol.build()
mf1 = scf.UHF(mol).run(conv_tol=1e-12)
mf1 = scf.addons.convert_to_ghf(mf1)

gcc1 = gccsd.GCCSD(mf1).run(conv_tol=1e-9)

class KnownValues(unittest.TestCase):
    def test_gccsd(self):
        self.assertAlmostEqual(gcc1.e_corr, -0.18212844850615587, 7)

    def test_ERIS(self):
        gcc = gccsd.GCCSD(mf1, frozen=4)
        numpy.random.seed(9)
        mo_coeff0 = numpy.random.random(mf1.mo_coeff.shape) - .9
        mo_coeff0[mf1.mo_coeff == 0] = 0
        mo_coeff1 = mo_coeff0.copy()
        mo_coeff1[-1,0] = 1e-12

        eris = gccsd._make_eris_incore(gcc, mo_coeff0)
        self.assertAlmostEqual(lib.finger(eris.oooo), -18.784809755855356, 9)
        self.assertAlmostEqual(lib.finger(eris.ooov),  10.318635295182752, 9)
        self.assertAlmostEqual(lib.finger(eris.oovv),  48.826269126647048, 9)
        self.assertAlmostEqual(lib.finger(eris.ovov), -2464.0817096151195, 9)
        self.assertAlmostEqual(lib.finger(eris.ovvv),  36.516396893446711, 9)
        self.assertAlmostEqual(lib.finger(eris.vvvv),  309.52000351959856, 9)

        eris = gccsd._make_eris_outcore(gcc, mo_coeff0)
        self.assertAlmostEqual(lib.finger(eris.oooo), -18.784809755855356, 9)
        self.assertAlmostEqual(lib.finger(eris.ooov),  10.318635295182752, 9)
        self.assertAlmostEqual(lib.finger(eris.oovv),  48.826269126647048, 9)
        self.assertAlmostEqual(lib.finger(eris.ovov), -2464.0817096151195, 9)
        self.assertAlmostEqual(lib.finger(eris.ovvv),  36.516396893446711, 9)
        self.assertAlmostEqual(lib.finger(eris.vvvv),  309.52000351959856, 9)

        eris = gccsd._make_eris_incore(gcc, mo_coeff1)
        self.assertAlmostEqual(lib.finger(eris.oooo), -18.784809755855356, 9)
        self.assertAlmostEqual(lib.finger(eris.ooov),  10.318635295182752, 9)
        self.assertAlmostEqual(lib.finger(eris.oovv),  48.826269126647048, 9)
        self.assertAlmostEqual(lib.finger(eris.ovov), -2464.0817096151195, 9)
        self.assertAlmostEqual(lib.finger(eris.ovvv),  36.516396893446711, 9)
        self.assertAlmostEqual(lib.finger(eris.vvvv),  309.52000351959856, 9)

        eris = gccsd._make_eris_outcore(gcc, mo_coeff1)
        self.assertAlmostEqual(lib.finger(eris.oooo), -18.784809755855356, 9)
        self.assertAlmostEqual(lib.finger(eris.ooov),  10.318635295182752, 9)
        self.assertAlmostEqual(lib.finger(eris.oovv),  48.826269126647048, 9)
        self.assertAlmostEqual(lib.finger(eris.ovov), -2464.0817096151195, 9)
        self.assertAlmostEqual(lib.finger(eris.ovvv),  36.516396893446711, 9)
        self.assertAlmostEqual(lib.finger(eris.vvvv),  309.52000351959856, 9)

    def test_spin2spatial(self):
        nocca, noccb = mol.nelec
        nvira = mol.nao_nr() - nocca
        nvirb = mol.nao_nr() - noccb
        numpy.random.seed(1)
        t1 = [numpy.random.random((nocca,nvira))*.1 - .1,
              numpy.random.random((noccb,nvirb))*.1 - .1]
        t2 = [numpy.random.random((nocca,nocca,nvira,nvira))*.1 - .1,
              numpy.random.random((nocca,noccb,nvira,nvirb))*.1 - .1,
              numpy.random.random((noccb,noccb,nvirb,nvirb))*.1 - .1]
        t2[0] = t2[0] - t2[0].transpose(1,0,2,3)
        t2[0] = t2[0] - t2[0].transpose(0,1,3,2)
        t2[2] = t2[2] - t2[2].transpose(1,0,2,3)
        t2[2] = t2[2] - t2[2].transpose(0,1,3,2)
        t1u = gcc1.spin2spatial(gcc1.spatial2spin(t1))
        t2u = gcc1.spin2spatial(gcc1.spatial2spin(t2))
        self.assertAlmostEqual(abs(t1[0] - t1u[0]).max(), 0, 12)
        self.assertAlmostEqual(abs(t1[1] - t1u[1]).max(), 0, 12)
        self.assertAlmostEqual(abs(t2[0] - t2u[0]).max(), 0, 12)
        self.assertAlmostEqual(abs(t2[1] - t2u[1]).max(), 0, 12)
        self.assertAlmostEqual(abs(t2[2] - t2u[2]).max(), 0, 12)

    def test_update_amps(self):
        mol = gto.M()
        nocc, nvir = 8, 14
        nmo = nocc + nvir
        nmo_pair = nmo*(nmo+1)//2
        mf = scf.GHF(mol)
        numpy.random.seed(12)
        mf._eri = numpy.random.random(nmo_pair*(nmo_pair+1)//2)
        mf.mo_coeff = numpy.random.random((nmo,nmo))
        mf.mo_energy = numpy.arange(0., nmo)
        mf.mo_occ = numpy.zeros(nmo)
        mf.mo_occ[:nocc] = 1
        vhf = numpy.random.random((nmo,nmo)) + numpy.random.random((nmo,nmo))+1j
        vhf = vhf + vhf.conj().T
        mf.get_veff = lambda *args: vhf
        cinv = numpy.linalg.inv(mf.mo_coeff)
        mf.get_hcore = lambda *args: (reduce(numpy.dot, (cinv.T*mf.mo_energy, cinv)) - vhf)
        nmo_pair = nmo*(nmo//2+1)//4
        mf._eri = numpy.random.random(nmo_pair*(nmo_pair+1)//2)
        mycc = gccsd.GCCSD(mf)
        eris = mycc.ao2mo()
        eris.oooo = eris.oooo + numpy.sin(eris.oooo)*1j
        eris.oooo = eris.oooo + eris.oooo.conj().transpose(2,3,0,1)
        eris.ooov = eris.ooov + numpy.sin(eris.ooov)*1j
        eris.oovv = eris.oovv + numpy.sin(eris.oovv)*1j
        eris.ovov = eris.ovov + numpy.sin(eris.ovov)*1j
        eris.ovov = eris.ovov + eris.ovov.conj().transpose(2,3,0,1)
        eris.ovvv = eris.ovvv + numpy.sin(eris.ovvv)*1j
        eris.vvvv = eris.vvvv + numpy.sin(eris.vvvv)*1j
        eris.vvvv = eris.vvvv + eris.vvvv.conj().transpose(2,3,0,1)
        a = numpy.random.random((nmo,nmo)) * .1
        eris.fock += a + a.T
        t1 = numpy.random.random((nocc,nvir))*.1 + numpy.random.random((nocc,nvir))*.1j
        t2 = (numpy.random.random((nocc,nocc,nvir,nvir))*.1 +
              numpy.random.random((nocc,nocc,nvir,nvir))*.1j)
        t2 = t2 - t2.transpose(0,1,3,2)
        t2 = t2 - t2.transpose(1,0,2,3)
        r1, r2 = mycc.vector_to_amplitudes(mycc.amplitudes_to_vector(t1, t2))
        self.assertAlmostEqual(abs(t1-r1).max(), 0, 14)
        self.assertAlmostEqual(abs(t2-r2).max(), 0, 14)

        t1a, t2a = mycc.update_amps(t1, t2, eris)
        self.assertAlmostEqual(lib.finger(t1a), 20.805393111419136-300.1138026015621j, 9)
        self.assertAlmostEqual(lib.finger(t2a),-313.54117398035567+8.3700078645035205j, 9)

    def test_rdm_real(self):
        nocc = 6
        nvir = 10
        mf = scf.GHF(mol)
        nmo = nocc + nvir
        npair = nmo*(nmo//2+1)//4
        numpy.random.seed(12)
        mf._eri = numpy.random.random(npair*(npair+1)//2)*.3
        hcore = numpy.random.random((nmo,nmo)) * .5
        hcore = hcore + hcore.T + numpy.diag(range(nmo))*2
        mf.get_hcore = lambda *args: hcore
        mf.get_ovlp = lambda *args: numpy.eye(nmo)
        mf.mo_coeff = numpy.eye(nmo)
        mf.mo_occ = numpy.zeros(nmo)
        mf.mo_occ[:nocc] = 1
        mf.e_tot = mf.energy_elec()[0]
        mycc = gccsd.GCCSD(mf)
        ecc, t1, t2 = mycc.kernel()
        l1, l2 = mycc.solve_lambda()
        dm1 = gccsd_rdm.make_rdm1(mycc, t1, t2, l1, l2)
        dm2 = gccsd_rdm.make_rdm2(mycc, t1, t2, l1, l2)
        nao = nmo // 2
        mo_a = mf.mo_coeff[:nao]
        mo_b = mf.mo_coeff[nao:]
        eri  = ao2mo.kernel(mf._eri, mo_a)
        eri += ao2mo.kernel(mf._eri, mo_b)
        eri1 = ao2mo.kernel(mf._eri, (mo_a,mo_a,mo_b,mo_b))
        eri += eri1
        eri += eri1.T
        eri = ao2mo.restore(1, eri, nmo)
        h1 = reduce(numpy.dot, (mf.mo_coeff.T.conj(), hcore, mf.mo_coeff))
        e1 = numpy.einsum('ij,ji', h1, dm1)
        e1+= numpy.einsum('ijkl,ijkl', eri, dm2) * .5
        self.assertAlmostEqual(e1, mycc.e_tot, 7)

        self.assertAlmostEqual(abs(dm2-dm2.transpose(1,0,3,2).conj()).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2-dm2.transpose(2,3,0,1)       ).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2+dm2.transpose(2,1,0,3)       ).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2+dm2.transpose(0,3,2,1)       ).max(), 0, 9)

    def test_rdm_complex(self):
        mol = gto.M()
        mol.verbose = 0
        nocc = 6
        nvir = 8
        mf = scf.GHF(mol)
        nmo = nocc + nvir
        numpy.random.seed(1)
        eri = (numpy.random.random((nmo,nmo,nmo,nmo)) +
               numpy.random.random((nmo,nmo,nmo,nmo))* 1j - (.5+.5j))
        eri = eri + eri.transpose(1,0,3,2).conj()
        eri = eri + eri.transpose(2,3,0,1)
        eri *= .1

        def get_jk(mol, dm, *args,**kwargs):
            vj = numpy.einsum('ijkl,lk->ij', eri, dm)
            vk = numpy.einsum('ijkl,jk->il', eri, dm)
            return vj, vk
        def get_veff(mol, dm, *args, **kwargs):
            vj, vk = get_jk(mol, dm)
            return vj - vk
        def ao2mofn(mos):
            return eri

        mf.get_jk = get_jk
        mf.get_veff = get_veff
        hcore = numpy.random.random((nmo,nmo)) * .2 + numpy.random.random((nmo,nmo))* .2j
        hcore = hcore + hcore.T.conj() + numpy.diag(range(nmo))*2
        mf.get_hcore = lambda *args: hcore
        mf.get_ovlp = lambda *args: numpy.eye(nmo)
        orbspin = numpy.zeros(nmo, dtype=int)
        orbspin[1::2] = 1
        mf.mo_coeff = lib.tag_array(numpy.eye(nmo) + 0j, orbspin=orbspin)
        mf.mo_occ = numpy.zeros(nmo)
        mf.mo_occ[:nocc] = 1
        mf.e_tot = mf.energy_elec(mf.make_rdm1(), hcore)[0]

        mycc = cc.GCCSD(mf)
        eris = gccsd._make_eris_incore(mycc, mf.mo_coeff, ao2mofn)
        mycc.ao2mo = lambda *args, **kwargs: eris
        mycc.kernel(eris=eris)
        mycc.solve_lambda(eris=eris)
        dm1 = mycc.make_rdm1()
        dm2 = mycc.make_rdm2()

        e1 = numpy.einsum('ij,ji', hcore, dm1)
        e1+= numpy.einsum('ijkl,ijkl', eri, dm2) * .5
        self.assertAlmostEqual(e1, mycc.e_tot, 7)

        self.assertAlmostEqual(abs(dm2-dm2.transpose(1,0,3,2).conj()).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2-dm2.transpose(2,3,0,1)       ).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2+dm2.transpose(2,1,0,3)       ).max(), 0, 9)
        self.assertAlmostEqual(abs(dm2+dm2.transpose(0,3,2,1)       ).max(), 0, 9)

    def test_rdm_vs_uccsd(self):
        mol = gto.Mole()
        mol.atom = [
            [8 , (0. , 0.     , 0.)],
            [1 , (0. , -0.757 , 0.587)],
            [1 , (0. , 0.757  , 0.587)]]
        mol.verbose = 5
        mol.output = '/dev/null'
        mol.basis = '631g'
        mol.spin = 2
        mol.build()
        mf = scf.UHF(mol).run()
        myucc = uccsd.UCCSD(mf)
        myucc.frozen = 1
        myucc.kernel()
        udm1 = myucc.make_rdm1()
        udm2 = myucc.make_rdm2()

        mf = scf.addons.convert_to_ghf(mf)
        mygcc = gccsd.GCCSD(mf)
        mygcc.frozen = 2
        ecc, t1, t2 = mygcc.kernel()
        l1, l2 = mygcc.solve_lambda()
        dm1 = gccsd_rdm.make_rdm1(mygcc, t1, t2, l1, l2)
        dm2 = gccsd_rdm.make_rdm2(mygcc, t1, t2, l1, l2)

        nao = mol.nao_nr()
        mo_a = mf.mo_coeff[:nao]
        mo_b = mf.mo_coeff[nao:]
        nmo = mo_a.shape[1]
        eri = ao2mo.kernel(mf._eri, mo_a+mo_b, compact=False).reshape([nmo]*4)
        orbspin = mf.mo_coeff.orbspin
        sym_forbid = (orbspin[:,None] != orbspin)
        eri[sym_forbid,:,:] = 0
        eri[:,:,sym_forbid] = 0
        hcore = scf.RHF(mol).get_hcore()
        h1 = reduce(numpy.dot, (mo_a.T.conj(), hcore, mo_a))
        h1+= reduce(numpy.dot, (mo_b.T.conj(), hcore, mo_b))
        e1 = numpy.einsum('ij,ji', h1, dm1)
        e1+= numpy.einsum('ijkl,ijkl', eri, dm2) * .5
        e1+= mol.energy_nuc()
        self.assertAlmostEqual(e1, mygcc.e_tot, 7)

        idxa = numpy.where(orbspin == 0)[0]
        idxb = numpy.where(orbspin == 1)[0]
        self.assertAlmostEqual(abs(dm1[idxa[:,None],idxa] - udm1[0]).max(), 0, 7)
        self.assertAlmostEqual(abs(dm1[idxb[:,None],idxb] - udm1[1]).max(), 0, 7)
        self.assertAlmostEqual(abs(dm2[idxa[:,None,None,None],idxa[:,None,None],idxa[:,None],idxa] - udm2[0]).max(), 0, 7)
        self.assertAlmostEqual(abs(dm2[idxa[:,None,None,None],idxa[:,None,None],idxb[:,None],idxb] - udm2[1]).max(), 0, 7)
        self.assertAlmostEqual(abs(dm2[idxb[:,None,None,None],idxb[:,None,None],idxb[:,None],idxb] - udm2[2]).max(), 0, 7)

        ut1 = [0] * 2
        ul1 = [0] * 2
        ut2 = [0] * 3
        ul2 = [0] * 3
        ut1[0] = myucc.t1[0] + numpy.cos(myucc.t1[0]) * .2j
        ut1[1] = myucc.t1[1] + numpy.cos(myucc.t1[1]) * .2j
        ul1[0] = myucc.l1[0] + numpy.cos(myucc.l1[0]) * .2j
        ul1[1] = myucc.l1[1] + numpy.cos(myucc.l1[1]) * .2j
        ut2[0] = myucc.t2[0] + numpy.sin(myucc.t2[0]) * .8j
        ut2[1] = myucc.t2[1] + numpy.sin(myucc.t2[1]) * .8j
        ut2[2] = myucc.t2[2] + numpy.sin(myucc.t2[2]) * .8j
        ul2[0] = myucc.l2[0] + numpy.sin(myucc.l2[0]) * .8j
        ul2[1] = myucc.l2[1] + numpy.sin(myucc.l2[1]) * .8j
        ul2[2] = myucc.l2[2] + numpy.sin(myucc.l2[2]) * .8j
        udm1 = myucc.make_rdm1(ut1, ut2, ul1, ul2)
        udm2 = myucc.make_rdm2(ut1, ut2, ul1, ul2)

        gt1 = mygcc.spatial2spin(ut1)
        gt2 = mygcc.spatial2spin(ut2)
        gl1 = mygcc.spatial2spin(ul1)
        gl2 = mygcc.spatial2spin(ul2)
        gdm1 = mygcc.make_rdm1(gt1, gt2, gl1, gl2)
        gdm2 = mygcc.make_rdm2(gt1, gt2, gl1, gl2)

        self.assertAlmostEqual(abs(gdm1[idxa[:,None],idxa] - udm1[0]).max(), 0, 9)
        self.assertAlmostEqual(abs(gdm1[idxb[:,None],idxb] - udm1[1]).max(), 0, 9)
        self.assertAlmostEqual(abs(gdm2[idxa[:,None,None,None],idxa[:,None,None],idxa[:,None],idxa] - udm2[0]).max(), 0, 9)
        self.assertAlmostEqual(abs(gdm2[idxa[:,None,None,None],idxa[:,None,None],idxb[:,None],idxb] - udm2[1]).max(), 0, 9)
        self.assertAlmostEqual(abs(gdm2[idxb[:,None,None,None],idxb[:,None,None],idxb[:,None],idxb] - udm2[2]).max(), 0, 9)

    def test_rdm_vs_rccsd(self):
        mol = gto.Mole()
        mol.atom = [
            [8 , (0. , 0.     , 0.)],
            [1 , (0. , -0.757 , 0.587)],
            [1 , (0. , 0.757  , 0.587)]]
        mol.verbose = 5
        mol.output = '/dev/null'
        mol.basis = '631g'
        mol.build()
        mf = scf.RHF(mol).run()
        myrcc = ccsd.CCSD(mf).run()
        rdm1 = myrcc.make_rdm1()
        rdm2 = myrcc.make_rdm2()

        mf = scf.addons.convert_to_ghf(mf)
        mygcc = gccsd.GCCSD(mf).run()
        dm1 = mygcc.make_rdm1()
        dm2 = mygcc.make_rdm2()

        nao = mol.nao_nr()
        mo_a = mf.mo_coeff[:nao]
        mo_b = mf.mo_coeff[nao:]
        nmo = mo_a.shape[1]
        eri = ao2mo.kernel(mf._eri, mo_a+mo_b, compact=False).reshape([nmo]*4)
        orbspin = mf.mo_coeff.orbspin
        sym_forbid = (orbspin[:,None] != orbspin)
        eri[sym_forbid,:,:] = 0
        eri[:,:,sym_forbid] = 0
        hcore = scf.RHF(mol).get_hcore()
        h1 = reduce(numpy.dot, (mo_a.T.conj(), hcore, mo_a))
        h1+= reduce(numpy.dot, (mo_b.T.conj(), hcore, mo_b))
        e1 = numpy.einsum('ij,ji', h1, dm1)
        e1+= numpy.einsum('ijkl,ijkl', eri, dm2) * .5
        e1+= mol.energy_nuc()
        self.assertAlmostEqual(e1, mygcc.e_tot, 7)

        idxa = numpy.where(orbspin == 0)[0]
        idxb = numpy.where(orbspin == 1)[0]
        trdm1 = dm1[idxa[:,None],idxa]
        trdm1+= dm1[idxb[:,None],idxb]
        trdm2 = dm2[idxa[:,None,None,None],idxa[:,None,None],idxa[:,None],idxa]
        trdm2+= dm2[idxb[:,None,None,None],idxb[:,None,None],idxb[:,None],idxb]
        dm2ab = dm2[idxa[:,None,None,None],idxa[:,None,None],idxb[:,None],idxb]
        trdm2+= dm2ab
        trdm2+= dm2ab.transpose(2,3,0,1)
        self.assertAlmostEqual(abs(trdm1 - rdm1).max(), 0, 6)
        self.assertAlmostEqual(abs(trdm2 - rdm2).max(), 0, 6)

        rt1 = myrcc.t1 + numpy.cos(myrcc.t1) * .2j
        rl1 = myrcc.l1 + numpy.cos(myrcc.l1) * .2j
        rt2 = myrcc.t2 + numpy.sin(myrcc.t2) * .8j
        rl2 = myrcc.l2 + numpy.sin(myrcc.l2) * .8j
        rdm1 = myrcc.make_rdm1(rt1, rt2, rl1, rl2)
        rdm2 = myrcc.make_rdm2(rt1, rt2, rl1, rl2)

        gt1 = mygcc.spatial2spin(rt1)
        gt2 = mygcc.spatial2spin(rt2)
        gl1 = mygcc.spatial2spin(rl1)
        gl2 = mygcc.spatial2spin(rl2)
        gdm1 = mygcc.make_rdm1(gt1, gt2, gl1, gl2)
        gdm2 = mygcc.make_rdm2(gt1, gt2, gl1, gl2)

        trdm1 = gdm1[idxa[:,None],idxa]
        trdm1+= gdm1[idxb[:,None],idxb]
        trdm2 = gdm2[idxa[:,None,None,None],idxa[:,None,None],idxa[:,None],idxa]
        trdm2+= gdm2[idxb[:,None,None,None],idxb[:,None,None],idxb[:,None],idxb]
        dm2ab = gdm2[idxa[:,None,None,None],idxa[:,None,None],idxb[:,None],idxb]
        trdm2+= dm2ab
        trdm2+= dm2ab.transpose(2,3,0,1)
        self.assertAlmostEqual(abs(trdm1 - rdm1).max(), 0, 9)
        self.assertAlmostEqual(abs(trdm2 - rdm2).max(), 0, 9)


if __name__ == "__main__":
    print("Tests for GCCSD")
    unittest.main()
