import unittest
import os
import sqlite3
import shutil
from database import (
    DatabaseManager, AuditRepository, SettingRepository, DependencyRepository,
    AssetRepository, LoanRepository, OfficialRepository, dict_compatibility_factory
)

class TestNexusDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_name = "test_inventory.db"
        cls.db_dir = os.path.dirname(__file__)
        cls.db_path = os.path.join(cls.db_dir, cls.db_name)
        
        prod_db_path = os.path.join(cls.db_dir, "inventory.db")
        if os.path.exists(prod_db_path):
            shutil.copy2(prod_db_path, cls.db_path)
            cls.copied = True
        else:
            cls.copied = False
            
        cls.db_manager = DatabaseManager(cls.db_name)
        cls.audit_repo = AuditRepository(cls.db_manager)
        cls.setting_repo = SettingRepository(cls.db_manager)
        cls.dep_repo = DependencyRepository(cls.db_manager)
        cls.asset_repo = AssetRepository(cls.db_manager, cls.setting_repo, cls.audit_repo)
        cls.loan_repo = LoanRepository(cls.db_manager)
        cls.official_repo = OfficialRepository(cls.db_manager)
        
        # Ensure row factory is set
        cls.db_manager.conn.row_factory = dict_compatibility_factory

    @classmethod
    def tearDownClass(cls):
        cls.db_manager.conn.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_a_add_and_fts_sync(self):
        """Test adding an asset and checking if FTS5 search index gets synced immediately."""
        test_code = "NX-TEST-999"
        test_desc = "Computador De Pruebas Unitarias FTS5"
        
        # Clean any old test records
        self.db_manager.cursor.execute("DELETE FROM assets WHERE CODIGO = ?", (test_code,))
        self.db_manager.conn.commit()
        
        data = (
            test_code, "101", "Equipos de Cómputo", test_desc,
            "Generic", "V1", "SN-999", "Negro", "50x50", "Ninguna",
            500000.0, 1, 500000.0, 0.0, 500000.0,
            "2026-06-07", "2026-06-07", 10, "Excelente", "Propio", "En Uso",
            "PRUEBAS"
        )
        
        self.asset_repo.add_asset(data)
        
        # Check FTS5
        self.db_manager.cursor.execute("SELECT rowid, DESCRIPCION FROM assets_search WHERE CODIGO = ?", (test_code,))
        fts_row = self.db_manager.cursor.fetchone()
        
        self.assertIsNotNone(fts_row, "FTS5 index should have created a row automatically via triggers.")
        self.assertEqual(fts_row['DESCRIPCION'], test_desc, "FTS5 description field must match.")
        
        # Query via instant_search
        results = self.asset_repo.instant_search("Pruebas Unitarias")
        self.assertTrue(len(results) > 0, "instant_search should locate the newly inserted asset.")
        self.assertEqual(dict(results[0])['code'], test_code)

    def test_b_update_and_fts_sync(self):
        """Test updating an asset and checking if FTS5 gets updated correctly."""
        test_code = "NX-TEST-999"
        new_desc = "Computador De Pruebas Unitarias FTS5 Modificado"
        
        self.db_manager.cursor.execute("SELECT id FROM assets WHERE CODIGO = ?", (test_code,))
        row = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(row)
        asset_id = row['id']
        
        # Update description
        success = self.asset_repo.update_asset(asset_id, {"description": new_desc})
        self.assertTrue(success)
        
        # Verify db
        self.db_manager.cursor.execute("SELECT DESCRIPCION FROM assets WHERE id = ?", (asset_id,))
        self.assertEqual(self.db_manager.cursor.fetchone()['DESCRIPCION'], new_desc)
        
        # Verify FTS5
        self.db_manager.cursor.execute("SELECT DESCRIPCION FROM assets_search WHERE rowid = ?", (asset_id,))
        self.assertEqual(self.db_manager.cursor.fetchone()['DESCRIPCION'], new_desc, "FTS5 search index description must be updated.")
        
        # Search for modified terms
        results = self.asset_repo.instant_search("Modificado")
        self.assertTrue(len(results) > 0, "Search index should find updated terms.")

    def test_c_transfer_and_fts_sync(self):
        """Test transferring an asset to another dependency and checking FTS5 sync."""
        test_code = "NX-TEST-999"
        new_dep = "NUEVA_AREA_TEST"
        
        self.db_manager.cursor.execute("SELECT id FROM assets WHERE CODIGO = ?", (test_code,))
        row = self.db_manager.cursor.fetchone()
        self.assertIsNotNone(row)
        asset_id = row['id']
        
        success = self.asset_repo.transfer_asset(asset_id, new_dep)
        self.assertTrue(success)
        
        # Verify FTS5
        self.db_manager.cursor.execute("SELECT UBICACION FROM assets_search WHERE rowid = ?", (asset_id,))
        self.assertEqual(self.db_manager.cursor.fetchone()['UBICACION'], new_dep, "FTS5 dependency field must update on transfer.")

    def test_d_partial_disposal_math(self):
        """Test partial disposal math: total values, depreciation rates, current values, and history rows."""
        # Create a multi-unit asset for testing math
        test_code = "NX-MATH-TEST"
        self.db_manager.cursor.execute("DELETE FROM assets WHERE CODIGO = ?", (test_code,))
        self.db_manager.conn.commit()
        
        data = (
            test_code, "101", "Muebles y Enseres", "Sillas de prueba matematica",
            "Metal", "S-20", "SN-MATH", "Gris", "30x30", "Ninguna",
            100000.0, 5, 500000.0, 150000.0, 350000.0,
            "2026-06-07", "2026-06-07", 10, "Excelente", "Propio", "En Uso",
            "PRUEBAS"
        )
        self.asset_repo.add_asset(data)
        
        # Retrieve the inserted id
        self.db_manager.cursor.execute("SELECT id FROM assets WHERE CODIGO = ? AND is_disposed = 0", (test_code,))
        asset_id = self.db_manager.cursor.fetchone()['id']
        
        # Dispose 2 of the 5 units (40% disposal)
        success = self.asset_repo.dispose_asset(asset_id, "Baja de 2 unidades", "2026-06-07", qty_to_dispose=2)
        self.assertTrue(success)
        
        # Verify original active asset values
        self.db_manager.cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        active_row = self.db_manager.cursor.fetchone()
        
        self.assertEqual(active_row['quantity'], 3)
        self.assertAlmostEqual(active_row['initial_total_value'], 300000.0)
        self.assertAlmostEqual(active_row['depreciation_rate'], 90000.0)
        self.assertAlmostEqual(active_row['current_value'], 210000.0)
        
        # Verify inserted historical disposed asset
        self.db_manager.cursor.execute("SELECT * FROM assets WHERE CODIGO = ? AND is_disposed = 1", (test_code,))
        disposed_row = self.db_manager.cursor.fetchone()
        
        self.assertIsNotNone(disposed_row)
        self.assertEqual(disposed_row['quantity'], 2)
        self.assertAlmostEqual(disposed_row['initial_total_value'], 200000.0)
        self.assertAlmostEqual(disposed_row['depreciation_rate'], 60000.0)
        self.assertAlmostEqual(disposed_row['current_value'], 140000.0)
        self.assertEqual(disposed_row['is_disposed'], 1)

    def test_e_dependency_asset_lifecycle(self):
        """Test adding an asset to a dependency, verifying it, and disposing it."""
        dep_name = "SALA_TEST_LIFECYCLE"
        
        # 1. Add Dependency
        success_dep = self.dep_repo.add_dependency(dep_name, "TEST_TYPE")
        self.assertTrue(success_dep, "Should be able to add a new dependency")
        
        # 2. Add Asset to Dependency
        test_code = "NX-DEP-TEST"
        self.db_manager.cursor.execute("DELETE FROM assets WHERE CODIGO = ?", (test_code,))
        self.db_manager.conn.commit()
        
        data = (
            test_code, "101", "General", "Activo de prueba dependencia",
            "Gen", "S1", "SN-DEP", "N/A", "N/A", "N/A",
            100.0, 1, 100.0, 0.0, 100.0,
            "2026-06-07", "2026-06-07", 5, "Bueno", "Propio", "En Uso",
            dep_name
        )
        success_asset = self.asset_repo.add_asset(data)
        self.assertTrue(success_asset, "Should be able to add asset to dependency")
        
        # Verify it appears in dependency list
        assets_in_dep = self.asset_repo.get_assets_by_dependency(dep_name)
        self.assertEqual(len(assets_in_dep), 1, "There should be 1 active asset in the dependency")
        
        asset_id = dict(assets_in_dep[0])['id']
        
        # 3. Dispose the asset
        success_dispose = self.asset_repo.dispose_asset(asset_id, "Baja de prueba", "2026-06-07")
        self.assertTrue(success_dispose, "Should be able to dispose the asset")
        
        # Verify it no longer appears as active
        assets_in_dep_after = self.asset_repo.get_assets_by_dependency(dep_name)
        self.assertEqual(len(assets_in_dep_after), 0, "There should be no active assets in the dependency after disposal")
        
        # Verify it appears in disposed list
        disposed_in_dep = self.asset_repo.get_disposed_assets_by_dependency(dep_name)
        self.assertEqual(len(disposed_in_dep), 1, "The asset should appear in the disposed list for the dependency")

    def test_g_atomic_backup_restore_and_vacuum(self):
        """Test native SQLite atomic backup, restoration, and database optimization."""
        backup_file = os.path.join(self.db_dir, "test_atomic_backup.db")
        if os.path.exists(backup_file):
            os.remove(backup_file)

        # 1. Test backup
        success_backup = self.db_manager.backup_to_file(backup_file)
        self.assertTrue(success_backup, "Native backup_to_file must succeed.")
        self.assertTrue(os.path.exists(backup_file), "Backup file must exist on disk.")

        # 2. Test restore
        success_restore = self.db_manager.restore_from_file(backup_file)
        self.assertTrue(success_restore, "Native restore_from_file must succeed.")

        # 3. Test vacuum / optimize
        success_opt = self.db_manager.optimize_database()
        self.assertTrue(success_opt, "Database optimize_database (VACUUM) must succeed.")

        if os.path.exists(backup_file):
            os.remove(backup_file)

class TestScrollHelper(unittest.TestCase):
    def test_scroll_helper_import_and_signature(self):
        """Test that scroll_helper module is available and follows SOLID signature."""
        from scroll_helper import enable_smooth_scroll
        import inspect
        sig = inspect.signature(enable_smooth_scroll)
        self.assertIn("canvas", sig.parameters)
        self.assertIn("container", sig.parameters)

if __name__ == "__main__":
    unittest.main()
