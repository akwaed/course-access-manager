import React, { useState, useEffect } from 'react';

const BASE_PATH = '/tcecontacts';
const API_BASE_URL = '/tcecontacts/api';

const CourseAccessManager = () => {
  const [contacts, setContacts] = useState([]);
  const [courses, setCourses] = useState([]);
  const [hierarchy, setHierarchy] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedView, setSelectedView] = useState('contacts');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      // For now, we'll use placeholder data
      // Replace with actual API calls when backend is ready
      setContacts([
        { id: 1, first_name: 'John', last_name: 'Doe', linkblue: 'jdoe', department: 'Computer Science' },
        { id: 2, first_name: 'Jane', last_name: 'Smith', linkblue: 'jsmith', department: 'Engineering' }
      ]);
      setCourses([
        { SECTION_KEY: 'CS101-001', TITLE: 'Introduction to Computer Science', PREFIX: 'CS', CLASS: '101' },
        { SECTION_KEY: 'CS201-001', TITLE: 'Data Structures', PREFIX: 'CS', CLASS: '201' }
      ]);
      setError(null);
    } catch (err) {
      setError('Failed to load data. Please try again later.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredContacts = contacts.filter(contact => 
    contact.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.linkblue?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.department?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredCourses = courses.filter(course =>
    course.SECTION_KEY?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.TITLE?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    course.PREFIX?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-800 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-800 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-800 text-white">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">University of Kentucky</h1>
          <h2 className="text-xl mt-2">Course Access Manager</h2>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-blue-700 text-white">
        <div className="container mx-auto px-4">
          <div className="flex space-x-4">
            <button
              onClick={() => setSelectedView('contacts')}
              className={`py-3 px-4 ${selectedView === 'contacts' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            >
              Contacts
            </button>
            <button
              onClick={() => setSelectedView('courses')}
              className={`py-3 px-4 ${selectedView === 'courses' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            >
              Courses
            </button>
            <button
              onClick={() => setSelectedView('hierarchy')}
              className={`py-3 px-4 ${selectedView === 'hierarchy' ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            >
              Hierarchy
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Search Bar */}
        <div className="mb-6">
          <input
            type="text"
            placeholder={`Search ${selectedView}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Content Display */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          {selectedView === 'contacts' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">Contacts</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LinkBlue</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredContacts.map((contact) => (
                      <tr key={contact.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          {contact.first_name} {contact.last_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {contact.linkblue}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {contact.department}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedView === 'courses' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">Courses</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Section Key</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prefix</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Class</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredCourses.map((course, index) => (
                      <tr key={course.SECTION_KEY || index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap font-medium">
                          {course.SECTION_KEY}
                        </td>
                        <td className="px-6 py-4">
                          {course.TITLE}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {course.PREFIX}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                          {course.CLASS}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedView === 'hierarchy' && (
            <div>
              <h3 className="text-2xl font-bold mb-4">Course Hierarchy</h3>
              <p className="text-gray-600">Hierarchy view coming soon...</p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white mt-12">
        <div className="container mx-auto px-4 py-6 text-center">
          <p>&copy; 2024 University of Kentucky. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default CourseAccessManager;
