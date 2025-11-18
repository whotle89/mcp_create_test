import { createClient } from '@supabase/supabase-js';
import { config } from 'dotenv';
import { resolve } from 'path';

// Load .env.local file
config({ path: resolve(process.cwd(), '.env.local') });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing environment variables!');
  console.error('NEXT_PUBLIC_SUPABASE_URL:', supabaseUrl);
  console.error('NEXT_PUBLIC_SUPABASE_ANON_KEY:', supabaseKey ? '[SET]' : '[NOT SET]');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkTables() {
  try {
    console.log('Checking Supabase tables...\n');

    // Get all tables from information_schema
    const { data: tables, error } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'public');

    if (error) {
      console.error('Error fetching tables:', error);

      // Alternative method: Try to query pg_tables
      console.log('\nTrying alternative method...\n');
      const { data: pgTables, error: pgError } = await supabase.rpc('get_tables');

      if (pgError) {
        console.error('Alternative method also failed:', pgError);
        console.log('\nPlease check your Supabase dashboard for table information.');
        console.log('Dashboard URL:', supabaseUrl.replace('.supabase.co', '.supabase.co/project/_/editor'));
      }
      return;
    }

    if (!tables || tables.length === 0) {
      console.log('No tables found in the public schema.');
      console.log('You may need to create tables first.');
      return;
    }

    console.log('Tables found:');
    tables.forEach((table: any) => {
      console.log(`- ${table.table_name}`);
    });

    // Get columns for each table
    console.log('\n--- Table Structures ---\n');
    for (const table of tables) {
      console.log(`\n📋 Table: ${table.table_name}`);

      const { data: columns, error: colError } = await supabase
        .from('information_schema.columns')
        .select('column_name, data_type, is_nullable, column_default')
        .eq('table_schema', 'public')
        .eq('table_name', table.table_name);

      if (colError) {
        console.error(`  Error fetching columns:`, colError);
        continue;
      }

      if (columns && columns.length > 0) {
        columns.forEach((col: any) => {
          const nullable = col.is_nullable === 'YES' ? 'nullable' : 'not null';
          const defaultVal = col.column_default ? ` (default: ${col.column_default})` : '';
          console.log(`  - ${col.column_name}: ${col.data_type} [${nullable}]${defaultVal}`);
        });
      }
    }

  } catch (error) {
    console.error('Unexpected error:', error);
  }
}

checkTables();
