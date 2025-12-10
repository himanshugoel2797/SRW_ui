// Python C API wrapper for the srwfast C library
// Provides a Python module named `nativelib` that exposes sum_array,
// scale_array, and load_file functions using Python.h + NumPy C API.

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include "fastlib.h"
#include <string>

static PyObject* py_sum_array(PyObject* /*self*/, PyObject* args) {
    PyObject* obj;
    if (!PyArg_ParseTuple(args, "O", &obj)) return NULL;
    PyObject* arr = PyArray_FROM_OTF(obj, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (!arr) return NULL;
    double* data = static_cast<double*>(PyArray_DATA(reinterpret_cast<PyArrayObject*>(arr)));
    npy_intp size = PyArray_SIZE(reinterpret_cast<PyArrayObject*>(arr));
    double s = fast_sum(data, static_cast<size_t>(size));
    Py_DECREF(arr);
    return PyFloat_FromDouble(s);
}

static PyObject* py_scale_array(PyObject* /*self*/, PyObject* args) {
    PyObject* obj;
    double scale;
    if (!PyArg_ParseTuple(args, "Od", &obj, &scale)) return NULL;
    PyObject* arr = PyArray_FROM_OTF(obj, NPY_DOUBLE, NPY_ARRAY_INOUT_ARRAY);
    if (!arr) return NULL;
    double* data = static_cast<double*>(PyArray_DATA(reinterpret_cast<PyArrayObject*>(arr)));
    npy_intp size = PyArray_SIZE(reinterpret_cast<PyArrayObject*>(arr));
    fast_scale(data, static_cast<size_t>(size), scale);
    // copy back if a temporary was made
    PyArray_ResolveWritebackIfCopy(reinterpret_cast<PyArrayObject*>(arr));
    PyObject* ret = arr; // return the possibly-updated array
    return ret;
}

static PyObject* py_load_file(PyObject* /*self*/, PyObject* args) {
    const char* path = nullptr;
    if (!PyArg_ParseTuple(args, "s", &path)) return NULL;
    char** headers = nullptr;
    size_t n_headers = 0;
    double* values = nullptr;
    size_t n_values = 0;
    int rc = fast_load_file(path, &headers, &n_headers, &values, &n_values);
    if (rc != 0) {
        PyErr_Format(PyExc_OSError, "fast_load_file failed, rc=%d", rc);
        return NULL;
    }
    PyObject* hlist = PyList_New((Py_ssize_t)n_headers);
    for (size_t i = 0; i < n_headers; ++i) {
        PyObject* s = PyUnicode_FromString(headers[i]);
        PyList_SET_ITEM(hlist, (Py_ssize_t)i, s);
    }
    // Create numpy array and copy values
    npy_intp dims[1] = { static_cast<npy_intp>(n_values) };
    PyObject* arr = PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    if (!arr) {
        fast_free_string_array(headers, n_headers);
        fast_free_double_array(values);
        PyErr_SetString(PyExc_MemoryError, "failed to allocate numpy array");
        return NULL;
    }
    if (n_values > 0) {
        void* dest = PyArray_DATA(reinterpret_cast<PyArrayObject*>(arr));
        std::memcpy(dest, values, n_values * sizeof(double));
    }
    // Free C-allocated memory
    fast_free_string_array(headers, n_headers);
    fast_free_double_array(values);
    PyObject* tup = PyTuple_New(2);
    PyTuple_SET_ITEM(tup, 0, hlist);
    PyTuple_SET_ITEM(tup, 1, arr);
    return tup;
}

static PyObject* py_load_lib(PyObject* /*self*/, PyObject* /*args*/) {
    Py_RETURN_NONE; // for compatibility with old nativelib.load_lib() in tests
}

static PyMethodDef NativelibMethods[] = {
    {"sum_array", (PyCFunction)py_sum_array, METH_VARARGS, "Return sum of a numeric array (NumPy array or sequence)"},
    {"scale_array", (PyCFunction)py_scale_array, METH_VARARGS, "Scale a numeric array in-place by a factor"},
    {"load_file", (PyCFunction)py_load_file, METH_VARARGS, "Load a numeric text file; returns (headers, values)"},
    {"load_lib", (PyCFunction)py_load_lib, METH_NOARGS, "Compatibility: ensure module is loaded (no-op)"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef nativelibmodule = {
    PyModuleDef_HEAD_INIT,
    "nativelib",
    "Native acceleration module for SRW tools (C++ / Python API)",
    -1,
    NativelibMethods
};

PyMODINIT_FUNC PyInit_nativelib(void) {
    PyObject* m;
    m = PyModule_Create(&nativelibmodule);
    if (m == NULL) return NULL;
    import_array();
    return m;
}
