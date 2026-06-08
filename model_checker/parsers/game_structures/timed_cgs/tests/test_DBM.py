import unittest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBM


class DBMTestCase(unittest.TestCase):
    def setUp(self):
        self.dbm1 = DBM(2)
        self.constraint_dbm = DBM(2)
        self.constraint_dbm.add_initial_constraint(1, 0, 20, "<")
        self.constraint_dbm.add_initial_constraint(2, 0, 20, "<=")
        self.constraint_dbm.add_initial_constraint(2, 1, 10, "<=")
        self.constraint_dbm.add_initial_constraint(1, 2, -10, "<=")

    def test_init(self):
        self.assertFalse(self.dbm1.is_empty(), "Initial DBM should be consistent")
        diag = self.dbm1.elements.diagonal()
        self.assertEqual(
            0, sum(entry.constant for entry in diag), "Diagonal should be zero"
        )
        for j in range(self.dbm1.size):
            self.assertEqual(
                0,
                self.dbm1.elements[0][j].constant,
                "All clocks are positive, 0 - xi ≤ 0",
            )

    def test_includes(self):
        self.assertTrue(self.dbm1.includes(self.dbm1), "Every DBM includes itself")
        closed_dbm = self.dbm1.close()
        self.assertTrue(self.dbm1.includes(closed_dbm), "Includes its canonical form")
        self.assertTrue(closed_dbm.includes(self.dbm1), "Reflexivity")

    def test_do_not_include(self):
        other_dbm = DBM(2)
        other_dbm.add_initial_constraint(0, 1, 1, "<=")
        self.assertFalse(other_dbm.includes(self.dbm1))
        self.dbm1.add_initial_constraint(0, 1, 1, "<")
        self.assertFalse(other_dbm.includes(self.dbm1))

    def test_close_throws_when_dbm_is_nonempty(self):
        dbm = DBM(3)
        dbm.add_initial_constraint(0, 1, 1, "<=")
        dbm.add_initial_constraint(1, 2, -1, "<=")
        dbm.add_initial_constraint(2, 3, -1, "<=")
        dbm.add_initial_constraint(3, 0, -1, "<=")
        self.assertRaises(ValueError, dbm.close)

    def test_close(self):
        expected_closure = DBM(2)
        expected_closure.add_constraint(1, 0, 10, "<=")
        expected_closure.add_constraint(2, 0, 20, "<=")
        expected_closure.add_constraint(2, 1, 10, "<=")
        expected_closure.add_constraint(1, 2, -10, "<=")
        self.assertEqual(expected_closure, self.constraint_dbm.close())

    def test_close_bouyer(self):
        """
        From Model Checking Timed Automata (P. Bouyer et al, 2018), p.24
        https://www.irif.fr/~francoisl/PUBLIS/BL-litron08.pdf
        """
        dbm = DBM(2)
        dbm.add_initial_constraint(0, 1, -3, "<=")
        dbm.add_initial_constraint(1, 2, 4, "<=")
        dbm.add_initial_constraint(2, 0, 5, "<=")
        actual_close = dbm.close()
        expected_close = DBM(2)
        expected_close.add_initial_constraint(0, 1, -3)
        expected_close.add_initial_constraint(1, 0, 9)
        expected_close.add_initial_constraint(1, 2, 4)
        expected_close.add_initial_constraint(2, 0, 5)
        expected_close.add_initial_constraint(2, 1, 2)
        self.assertEqual(actual_close, expected_close)

    def test_up_preserves_canonicity(self):
        dbm = self.constraint_dbm.close()
        dbm.up()
        self.assertEqual(dbm, dbm.close(), "Operation preserves canonical form")

    def test_inter(self):
        self.dbm1.add_constraint(1, 2, 1)
        self.assertEqual(self.dbm1.elements[1][2].constant, 1)
        self.assertEqual(self.dbm1.elements[1][2].operator, "<=")

        self.dbm1.add_constraint(2, 1, -10)
        self.assertNotEqual(self.dbm1.elements[2][1].constant, 10)
        self.assertEqual(
            self.dbm1.elements[0][0].constant,
            -1,
            "Adding a non-satisfiable constraint makes the DBM inconsistent",
        )

    def test_reset(self):
        self.constraint_dbm.reset(1, 5)
        self.assertEqual(self.constraint_dbm.elements[1][0].constant, 5)
        self.assertEqual(self.constraint_dbm.elements[0][1].constant, -5)
        self.assertEqual(self.constraint_dbm, self.constraint_dbm.close())

    def test_normalize(self):
        # x >= 1 and x <=3 and y>=2 and y<=3; 1 <= x <=3 ^ 2 <= y <=3
        dbm = DBM(2)
        dbm.add_constraint(1, 0, 3, "<=")
        dbm.add_constraint(0, 1, -1, "<=")
        dbm.add_constraint(2, 0, 3, "<=")
        dbm.add_constraint(0, 2, -2, "<=")
        dbm.k_normalize(
            [2, 1]
        )  # assume the model has these as max constraints, per x and y respectively
        expected_dbm = DBM(2)
        expected_dbm.add_constraint(0, 1, -1, "<=")
        expected_dbm.add_constraint(0, 2, -1, "<")
        expected_dbm.add_constraint(1, 2, 1, "<=")
        self.assertEqual(expected_dbm, dbm)

    def test_relax(self):
        expected = DBM(2)
        expected.add_initial_constraint(2, 0, 20, "<=")
        expected.add_initial_constraint(2, 1, 20, "<=")
        actual = self.constraint_dbm.get_free(1)
        self.assertEqual(expected, actual)

    def test_copy(self):
        self.assertEqual(self.dbm1, self.dbm1.copy())

    def test_add_constraint(self):
        dbm = DBM(2)  # x0, x, z
        # at s0 we have x<=5 as invariant, x>=5,x:=0 as guard and reset:
        dbm.add_constraint(1, 0, 5)
        dbm.add_constraint(0, 1, -5)
        dbm.reset(1)
        dbm.add_constraint(0, 2, -5, "<")


if __name__ == "__main__":
    unittest.main()
